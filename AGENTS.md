I want to create a FastAPI application that gives us status information about a computer, for example:

- Disk space used
- CPU status
- Network usage

(If you can think of other useful things to monitor, that's fine with me!)

It should be possible to go to one of the endpoints for this FastAPI server, and then get up-to-date information about the computer's status.

Make sure that it provides the API documentation/testing facilities that FastAPI normally gives us.

Some answers:

1. Ignore authentication. My life is an open book!
2. We should have separate endpoints for each piece of info
3. For now, we can accept any HTTP request, perhaps remote and perhaps local
4. Yes, memory, running processes, etc. are all good!

## Data and Pandas

- Use Pandas 3.0 syntax, especially pd.col, whenever possible.
- Use categories to reduce the size of text columns
- If you use df.info or df.memory_usage, make sure to use "deep", to get the true memory usage.
- Convert columns to the minimum possible dtype; check appropriateness and the min/max values in a column before doing this.
- Don't assign to any variables beyond the data frame you create unless you have no other options. Assign to a variable _once_ and use method chaining to extract and graph what you want.
- Use method chaining, using loc, assign, and pipe.
- Use Plotly for plotting. Avoid Matplotlib, Seaborn, and the Pandas API -- unless Plotly doesn't support what you want to do, then you can use the Pandas API.
- If you're iterating over a data frame with a "for" loop, then you're almost certainly doing something wrong. Find another way, unless you have no other options.
