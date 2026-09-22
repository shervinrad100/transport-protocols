# transport-protocols
 Learning some networking


I'm going to dig deep into how data is transferred between devides as if it's 1990 and we are building everything from scratch. 

This means that I need to understand the various layers in the OSI model and if needed either write those connections myself or use kernels and drivers that already exists.

Going to start easy and see how interested I get. 

Ideas so far:
- Sockets (TCP)
- HTTP(S)
- gRPC
- PubSub (not really a protocol but might as well chuck it in here)



# OWASP top 10

1. Broken access control
2. Security misconfiguration
3. Software supply chain failuers
4. Cryptographic failuers
5. Injection
6. Insecure design
7. Identification and authentication failures
8. Software and data integrity failures
9. Logging and alerting failures
10. Mishandling of exceptional situations

## 1. Broken access control
When someone can access data that they're not supposed to. 
One attack is called **Indirect Object Referencing (IDOR)**. Let's say you log in and the URL is `https://example.com&id=123`.if you're able to change the URL to `https://example.com&id=admin` or `https://example.com&id=321` and if you're able to access something that you're not supposed to then you have exploited a broken access control. This happens when your program is poorly built and doesn't check for access properly. 
The types of attack that you can exploit here are:
- path traversal
- privilaged escalation
- missing object/function level auth

Best found with Static Application Security Testing or Dynamic Application Security Testing. 

## 2. Security misconfiguration
This comes from poor DevOps where you may expose a surface area to attack. For example having your S3 buckets public and they can attack your infrastructure. 

You can fix this with IaC scanning, or Cloud Security Posture Management.

## 3. Software supply chain failuers
This is what happened with the attack on Linux where the attacker was building a backdoor to XZ Utils over years. And then all the Linux machines would be exposed because everyone uses that package. But this can also be in your IDE extensions. 

It can be fixed with Software Composition Analysis which searches all your dependencies and then sees if it has any vulnerabilities. 


## 4. Cryptographic failuers
This is when you use old hash functions that can be broken given the modern technology and processing power. This can also mean reusing passwords or not encrypting data in transit. 

Fixed with Static Application Security testing.


## 5. Injection
This is either SQL injection, cross-site scripting. 

We fix this with better design by escaping the user inputs and we have to make sure it happns both on the frontend (JS on browser) and backend (APIs). 


