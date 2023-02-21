# CS 262 Chat Application Engineering Notebook

## Installation & Setup

We offer multiple installation modalities:

### Conda
```
conda env create -f environment.yml
conda activate cs262ps1
```

### Pip

```
pip install -r requirements.txt
```

### Manual Installation

If you prefer an alternate method of installation, these are the dependencies: 
- Python 3.8+ (3.7 should work too)
- grpcio
- protobuf

# Design Notes

> Initial Considerations: As we began considering this project, we began with a simple socket design... we then had XYZ concerns, and thought of ABC questions. 

## Wire Protocol Design

> **Protocol support for multiple message sizes:** 

```
(1) 1 byte version #
(2) 1 byte action #
(3) 4 bytes size of body
(4) [size] bytes body
(5) 16 bytes of authentication, if necessary
```

We don't send strings! 

## Separation of Concerns

Client CLI/ server / and how that plays into the wire protocol. 

## Handling Multiple Connections

Threading, watchdogs, etc. 

> **Graceful Exits**: 

Closing sockets: 

https://docs.python.org/3/howto/sockets.html#when-sockets-die

## Passwords

We added passwords. Explain authentication token. 

# Unit Tests

We created these unit tests:
- A
- B
- C

# GRPC vs Naive Implementations

Areas to cover:
- Packet size
- Code simplicity
- Focus on designing the most optimized wire protocol possible
    - Design experience with sending strings over the wire protocol


