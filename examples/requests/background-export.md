Build a background report export flow. A user requests an export from a report page. The system queues the job, generates a CSV in the background, stores the file, notifies the user when ready, and lets them download it.

If generation fails, the queue is unavailable, storage is unavailable, or notification delivery fails, show a reviewable failure path and let the user retry when appropriate.

Model the async happy path and the high-priority dependency failures.
