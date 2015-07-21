How to make plugins
-------------------
Just make a python script, that script will get run every time somebody says a line / the hook gets called.  
The following variables will be initialized:  
* chan - the channel the message was sent in
* ident - the identity of the poster
* nick - the nick of the poster
* message - the whole message sent
* admin - True of False if the chatter is an admin
* sql - a mysql handler
* command - everything from message up to the first space
* args - everything from message after the command
* hook - boolean: if the script got called due to a hook
The following python libraries are already imported:  
* json
* HTMLParser
* re
* time
* random
* socket
* urllib
* math

To send a message:  
You have the function send, so like send("blah") will send a message right back to that channel.  
If it is run as a hook you will need to specify the network and channel, for example send("omninet","blah","#spam")
