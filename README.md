# scraper

# turn on venv
# python3.11 -m venv /Users/kennethchiu/develop_kenneth/scraper
# source bin/activate
# pip install .

# user can now run scraper and api per entry_points in setup.py
# web-scraper
# web-api



# thoughts

# db
# using sqlite because part of Python's standard library, simple and easy 

# future thoughts
# in later iterations, I would use aws infrastructure: Scraper code would be added to AWS lambda with 
# such that the aws lambda function would be triggered by the AWS SQS queue.
# depending on the use case, we can use dynamo db to store the data if the scraped data 
# is only going to be used as a third party tool for sales or some other team
# or rds if these scraped links are going to be used elsewhere in the tech stack. 




# places to improve

1. clean up the page source and to extract only visible text, and remove any extra characters.