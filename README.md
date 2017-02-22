# ETH Advanced Systems Lab project (Autumn 2016)
The project consists of the design and development of a middleware platform for key-value stores as well as the evaluation and analysis of its performance, and development of an analytical model of the system, and an analysis of how the model predictions compare to the actual system behavior. The middleware performs load balancing operations by steering traffic to different servers depending on the request content, and also performs primary-secondary replication.

## Milestone 1
In the first milestone, we provide a stable implementation of the system, able to forward requests to servers, and collect results. Its performance measured in a 1 hour trace that shows throughput and response time plotted over time.

## Milestone 2
In the second milestone we conduct a detailed experimental evaluation of the system, and answer the following questions:
* How does a detailed time-breakdown of different operations look like? Are requests spending more time queueing in the system than executing?
* What is the maximum throughput of the system? In what configuration is this throughput achieved?
* How does the workload (ratio of reads over writes) impact performance?
* What is the impact of the replication factor on the system? Is there a point where replication becomes so expensive that it limits the overall performance of the system?
* What is the most time-consuming operation for read and write requests?

## Milestone 3
In the final milestone we develop an analytical queuing model for each component of the system and for the system as a whole. Using the model, we derive the performance characteristics that the model predicts and compare them with the results obtained in milestones 1 and 2. We explain where the model and data match and where they do not match, including sufficiently detailed explanations of the code/system/hardware characteristics behind the observed behavior.
