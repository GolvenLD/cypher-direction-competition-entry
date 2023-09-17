# cypher-direction-competition-entry
My entry to the cypher direction competition by Tomaz Bratanic, last commits at 5:50 EST.

This solution is regex only - no external cypher parser! :) 

There are a couple of shortcomings that I would like to attend to after the competition (for the sake of submitting on time):
- It would be preferable if, just like the nodes, if the type of the relationship is not explicit, the script attempts to find the type elsewhere in the cypher statement
- The variable length relationships need more love. What would be ideal would be to check if, depending on the relationships in the schema, a certain number of jumps is possible at all. If the relationship is of one type, then the length of the relationship needs to be even if the couple cases in the examples. I would have needed more time/examples.

Thank you again to Tomaz for organizing this competition, I really enjoyed the challenge!
