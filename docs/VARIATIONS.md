# Deployment and protocol variations

The package separates three enforcement-timing profiles—blocked path, pre-routing authorization and absent path—from seven possible transport or assurance bindings: SIP/SBC, STIR/PASSporT identity input, HTTP/CPaaS, WebRTC/TURN, messaging/notification, federated edge and high-assurance/attested enforcement.

Configuration files describe placement, identity input and the limit of each claim. They are implementation examples, not registered protocol elements or assertions of working-group adoption.

Absent-path behavior is the strongest claim and requires closure of equivalent paths. If an ordinary number, SIP URI, alternate API, relay, forwarding rule, messaging address or notification service bypasses the check, the implementation can claim only the earliest boundary it actually controls.
