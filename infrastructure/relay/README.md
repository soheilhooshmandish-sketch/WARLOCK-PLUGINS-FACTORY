\# Warlock Relay



The relay is the boundary between an external control plane and the

Warlock Local Agent.



\## Security model



The relay must:



1\. Never expose port 8765 directly to the public internet.

2\. Require strong authentication for every request.

3\. Forward only allowlisted operations.

4\. Never provide arbitrary shell execution.

5\. Preserve the Local Agent workspace boundary.

6\. Record security-relevant requests.

7\. Fail closed when configuration or authentication is missing.



\## Current state



The current implementation is local-only.



The Local Agent listens on:



&#x20;   http://127.0.0.1:8765



The gateway communicates with the Local Agent using:



&#x20;   WARLOCK\_AGENT\_TOKEN



No public tunnel or internet-facing listener is configured yet.



\## Future deployment



A production relay requires an explicitly selected network provider or

hosted gateway.



The provider must support authenticated outbound connectivity without

requiring the Local Agent port to be publicly exposed.



Provider credentials must never be committed to Git.

