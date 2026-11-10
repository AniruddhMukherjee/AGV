"""Leader numbers each request; everyone applies them in that order.

Requirement covered: reliable ordered multicast
Owner: (assign a group member)

What goes here:
- Sequence numbers from the leader
- Followers detect missing numbers and ask for a resend
- Apply requests strictly in order
"""
