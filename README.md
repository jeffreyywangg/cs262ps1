# CS262 PS 1 Spec

Part 1:

For the first design exercise, you will develop a simple chat application. This will be a client/server application, with the following functions:

1. Create an account. You must supply a unique user name.
2. List accounts (or a subset of the accounts, by text wildcard)
3. Send a message to a recipient. If the recipient is logged in, deliver immediately; otherwise queue the message and deliver on demand. If the message is sent to someone who isn't a user, return an error message
4. Deliver undelivered messages to a particular user
5. Delete an account. You will need to specify the semantics of what happens if you attempt to delete an account that contains undelivered message.

The purpose of this assignment is to get you to design a wire protocol. So the solution is not to go looking for a library that will do this work for you. You should use sockets and transfer buffers (of your definition) between the machines.

You will need to write a specification of the wire protocol used in the system, and then build a client and server that use that protocol. It should be possible for multiple clients to connect to the server at the same time; you can assume a single instance of the server is all that is needed at this point. 

Build this in a repo on github that you make publicly available. The repo should include a README file that gives a set of instructions on setting up the client and server so that the system can be run. Part of your grade will depend on how well the code that you provide is documented. You may write you client and server in any of (or any combination of) python, C, C++, Java, or C#. Any other language requires the explicit permission of the instructor, which you won't get. Keep a notebook for what decisions you made, and why you made them the way you did, and any interesting observations that come up along the way.

You may turn in either a link to your repository (which should then be a public repo; "public" in this case just means open to the Harvard community) or as a tar or zip archive of the final result.

Please do not include your name in the files; we will be making use of anonymous peer reviewing for this (and other) assignments. Your code will be reviewed by the students in another group; part of that review will be following your instructions to set up and test the system that you built. This review will be part of the grade that your group gets for this assignment.

Part 2:

Re-implement (or alter) the application you built in Part 1 using gRPC. Add to your notebook comparisons over the complexity of the code, any performance differences, and the size of the buffers being sent back and forth between the client and the server. 
