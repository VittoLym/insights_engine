1/ "429 RESOURCE_EXHAUSTED" is not a bug; it is a diagnostic signal. If your system crashes when an upstream API throttles you, your architecture isn't resilient—it’s brittle. Senior engineers build for the quota, not the happy path.

2/ Implement Exponential Backoff with Jitter. Immediate retries turn a minor throttle into a self-inflicted DDoS. Use the `retryDelay` field provided in the error response—in this case, 10s—and add randomness to the interval to prevent "thundering herd" synchronization issues.

3/ Use the Circuit Breaker pattern. If you are consistently hitting resource limits, stop the bleeding. Open the circuit to prevent wasting internal compute and memory on requests destined to fail. This preserves your system's stability while the upstream provider resets.

4/ Shape traffic at the edge. Don't let your internal services dictate the request volume to a third-party API. Implement a local rate limiter using a Token Bucket or Leaky Bucket algorithm. Fail fast locally at the gateway rather than waiting for a remote 429.

5/ Resilience is the art of failing gracefully. When the Gemini API hits a hard limit, your system should have a fallback—whether that is a secondary provider, a cached response, or a queued background job. 

How are you handling LLM rate limits in production? Drop a comment below.