from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from collections import Counter
from app.database import get_db
from trip_plan.models import Group, GroupMember, GroupVote, Trip
from trip_plan.schemas import (
    GroupCreateRequest, GroupCreateResponse,
    GroupVoteRequest, GroupVoteResponse,
    GroupResultResponse, GroupDetailResponse
)
import uuid
import random
import string
import os

router = APIRouter(prefix="/groups", tags=["Group Planning"])

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@router.post("/create", response_model=GroupCreateResponse)
def create_group(request: GroupCreateRequest, db: Session = Depends(get_db)):
    # Generate unique short code
    short_code = generate_short_code()
    while db.query(Group).filter(Group.short_code == short_code).first():
        short_code = generate_short_code()

    # Create Group
    new_group = Group(
        leader_id=request.leader_id,
        name=request.group_name,
        short_code=short_code,
        from_city=request.from_city,
        expected_count=request.expected_count,
        destination_options=request.destination_options
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # Add Members
    # Add leader as a member too
    leader_member = GroupMember(group_id=new_group.id, email=request.leader_email, status="joined")
    db.add(leader_member)
    
    # Optional: Add invited members if provided
    if request.members:
        for email in request.members:
            if email != request.leader_email:
                member = GroupMember(group_id=new_group.id, email=email, status="invited")
                db.add(member)
    
    db.commit()
    
    # Generate Link
    link = f"https://travelorbit.com/vote/{short_code}" 
    
    return GroupCreateResponse(
        group_id=new_group.id,
        shareable_link=link,
        message=f"Group '{request.group_name}' created! Share the link with friends."
    )

@router.get("/{group_id}", response_model=GroupDetailResponse)
def get_group_details(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members_data = [{"email": m.email, "status": m.status} for m in group.members]
    votes_data = [{"voter": v.voter_email, "destination": v.destination} for v in group.votes]
    
    return GroupDetailResponse(
        group_id=group.id,
        name=group.name,
        leader_id=group.leader_id,
        members=members_data,
        votes=votes_data,
        destination_options=group.destination_options
    )

@router.get("/code/{short_code}", response_model=GroupDetailResponse)
def get_group_by_code(short_code: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.short_code == short_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members_data = [{"email": m.email, "status": m.status} for m in group.members]
    votes_data = [{"voter": v.voter_email, "destination": v.destination} for v in group.votes]
    
    return GroupDetailResponse(
        group_id=group.id,
        name=group.name,
        leader_id=group.leader_id,
        members=members_data,
        votes=votes_data,
        destination_options=group.destination_options
    )

@router.post("/{group_id}/vote", response_model=GroupVoteResponse)
def submit_vote(group_id: str, request: GroupVoteRequest, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Auto-add as member if they vote and are not in the list
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.email == request.voter_email).first()
    if not member:
        member = GroupMember(group_id=group_id, email=request.voter_email, status="joined")
        db.add(member)
    else:
        member.status = "joined"
    
    # Check if already voted
    existing_vote = db.query(GroupVote).filter(GroupVote.group_id == group_id, GroupVote.voter_email == request.voter_email).first()
    
    vote_id = None
    if existing_vote:
        # Update vote
        existing_vote.destination = request.destination
        existing_vote.budget = request.budget
        existing_vote.start_date = request.start_date
        existing_vote.end_date = request.end_date
        existing_vote.activities = request.activities
        existing_vote.voter_name = request.voter_name
        existing_vote.voter_phone = request.voter_phone
        vote_id = existing_vote.id
    else:
        new_vote = GroupVote(
            group_id=group_id,
            voter_email=request.voter_email,
            voter_name=request.voter_name,
            voter_phone=request.voter_phone,
            destination=request.destination,
            budget=request.budget,
            start_date=request.start_date,
            end_date=request.end_date,
            activities=request.activities
        )
        db.add(new_vote)
        db.flush() # to get id
        vote_id = new_vote.id
    
    db.commit()

    # Check if voting is complete
    total_votes = db.query(GroupVote).filter(GroupVote.group_id == group_id).count()
    if group.expected_count and total_votes >= group.expected_count:
        # Trigger auto-conversion
        _convert_group_to_trip_logic(group_id, db)
    
    return GroupVoteResponse(
        message="Vote submitted successfully!",
        vote_id=vote_id
    )

def _convert_group_to_trip_logic(group_id: str, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group or not group.votes:
        return None
        
    votes = group.votes
    destinations = [v.destination for v in votes if v.destination]
    budgets = [v.budget for v in votes if v.budget]
    dates = [v.start_date for v in votes if v.start_date]
    
    most_common_dest = Counter(destinations).most_common(1)[0][0] if destinations else "Unknown"
    most_common_budget = Counter(budgets).most_common(1)[0][0] if budgets else "Moderate"
    
    # Calculate majority dates (start and end)
    date_ranges = []
    for v in votes:
        if v.start_date and v.end_date:
            date_ranges.append((v.start_date, v.end_date))
            
    most_common_range = Counter(date_ranges).most_common(1)[0][0] if date_ranges else (None, None)
    start_date, end_date = most_common_range
    
    duration_days = 3 # Default
    if start_date and end_date:
        delta = end_date - start_date
        duration_days = delta.days
        if duration_days < 1: duration_days = 1
    
    # Collect interests from votes
    all_activities = []
    for v in votes:
        if v.activities:
            all_activities.extend(v.activities)
    most_common_activities = [item for item, count in Counter(all_activities).most_common(5)]

    # Collect passengers
    passengers = []
    contact_phone = None
    for v in votes:
        passengers.append({
            "name": v.voter_name or v.voter_email.split('@')[0],
            "email": v.voter_email,
            "phone": v.voter_phone,
            "role": "adult" # Default role
        })
        if v.voter_phone and not contact_phone:
            contact_phone = v.voter_phone

    # Use stored group details
    from_city = group.from_city or "Unknown"
    adults_count = len(passengers)
    
    # Check if trip already exists for this group (to avoid duplicates)
    # We can use a naming convention or check if leader has a trip with this title recently created?
    # Better: Add group_id to Trip model? Or just create a new one.
    # For now, we'll just create a new one.
    
    new_trip = Trip(
        id=uuid.uuid4().hex,
        register_id=group.leader_id,
        email=group.members[0].email if group.members else "unknown",
        from_city=from_city,
        to_city=most_common_dest,
        budget_level=most_common_budget,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration_days,
        party_type="friends",
        adults_count=adults_count,
        interests=most_common_activities, # Added interests
        status="planned", # Ready for payment
        title=f"Group Trip to {most_common_dest}",
        passengers=passengers,
        contact_phone=contact_phone
    )
    
    db.add(new_trip)
    db.commit()
    return new_trip

@router.get("/{group_id}/result", response_model=GroupResultResponse)
def get_group_result(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    votes = group.votes
    if not votes:
        return GroupResultResponse(
            group_id=group.id,
            group_name=group.name,
            most_voted_destination=None,
            most_voted_budget=None,
            most_voted_dates=None,
            most_voted_activities=[],
            total_votes=0,
            message="No votes yet."
        )
    
    # Calculate majority
    destinations = [v.destination for v in votes if v.destination]
    budgets = [v.budget for v in votes if v.budget]
    dates = [f"{v.start_date} to {v.end_date}" for v in votes if v.start_date and v.end_date]
    
    all_activities = []
    for v in votes:
        if v.activities:
            all_activities.extend(v.activities)
            
    most_common_dest = Counter(destinations).most_common(1)[0][0] if destinations else None
    most_common_budget = Counter(budgets).most_common(1)[0][0] if budgets else None
    most_common_dates = Counter(dates).most_common(1)[0][0] if dates else None
    
    # Top 3 activities
    most_common_activities = [item for item, count in Counter(all_activities).most_common(3)]
    
    return GroupResultResponse(
        group_id=group.id,
        group_name=group.name,
        most_voted_destination=most_common_dest,
        most_voted_budget=most_common_budget,
        most_voted_dates=most_common_dates,
        most_voted_activities=most_common_activities,
        total_votes=len(votes),
        message="Group results calculated."
    )

@router.post("/{group_id}/convert-to-trip", response_model=dict)
def convert_group_to_trip(group_id: str, db: Session = Depends(get_db)):
    trip = _convert_group_to_trip_logic(group_id, db)
    if not trip:
        raise HTTPException(status_code=400, detail="Could not convert group to trip (no votes or group not found)")
    
    return {"trip_id": trip.id, "message": "Trip created from group results"}

# Serve the voting page for the short link
# This route needs to be mounted at the root level or handled specially.
# Since this router has prefix="/groups", this would be /groups/vote/{short_code}
# But the user wants /vote/{short_code}.
# I will add a separate router or just a route in main.py for this.
# However, I can't easily modify main.py to add a route that depends on logic here without circular imports if I'm not careful.
# But I can just return the file content here if I change the prefix or add it to main.
