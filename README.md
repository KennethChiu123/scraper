# scraper

# setup instructions
1. source bin/activate (Turn on venv)
2. pip install . (installs all requirements and sets up entry points in setup.py)
3. web-scraper (to run web scraper)
4. web-api (to run api)
5. change configs if necessary(config.json)
```
 scraper % web-api      
 * Serving Flask app 'api.app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
127.0.0.1 - - [06/Dec/2024 22:05:53] "GET /scraped_links HTTP/1.1" 200 -
127.0.0.1 - - [06/Dec/2024 22:07:04] "GET /scraped_links/contact HTTP/1.1" 200 -
```


# process
1. I did some research on web scraping and decided I wanted to use Python and requests/beautifulsoup to pull the page source of the target site.
2. I needed a way to classify and rank the links by relevance so I found https://huggingface.co/tasks/zero-shot-classification and used it here. (I couldve researched other ways to do this, and there's probably tradeoffs)
3. Used sqlite to save the data as it's already part of python's standard library. 
4. Used flask to set up a simple api. Not well defined so I just set up two basic endpoints for now. 
5. added some improvements such as proxy and random user agent to mitigate chances of being flagged or ip blocked. 
6. added selenium as I found it got around cloudflare and to scrape fully rendered pages
7. web scraping was slow as it resembles a tree diagram. I added workers to speed up the process of scraping multiple pages and childs of those pages. 
8. restructured the code to separate the api functionality from the fetching and the scraping. 


# places to improve

1. clean up the page source and to extract only visible text, and remove any extra characters. Perhaps this would improve the score of the scraped site. 
2. research another nlp or use another ML model or use OpenAI. There are probably trade offs in terms of cost and time and performance. 
3. I've already structured it with the event queue in python, but if I were to deploy this in production, 
I would likely host this on an AWS lambda and have that lambda function triggered by an AWS SQS queue. After every url is scraped, all downstream urls are fired back into the SQS queue where it would trigger the lambda again. There would likely need to be an extra db connection to check if any of these downstream urls already exist in the db to prevent circular loops. (also a convenient place to add a cache)
4. sqlite was defaulted as the db of choice, but in an AWS environment, we'd likely use something like dynamo db as its fast and highily avaiable and scalable as we don't know how many sites we'll scrape. if we plan to use these sites in an internal capacity, we can use a mysql rds. 
5. build out a more robust api. I didn't have too much direction with this part, so it's quite minimal. 


API USAGE: 
1. http://127.0.0.1:5000/scraped_links will retrieve all links: where the highest relevance score is at the top

example: 
```
[
  {
    "classification": "ACFr",
    "id": 2,
    "relevance_score": 0.27340826392173767,
    "summary": " The City of Ann Arbor\u2019s mission is to deliver exceptional services that sustain and enhance a vibrant, safe and diverse community . The city has a Vision Zero goal to eliminate fatalities and serious injuries resulting from traffic crashes by 2030 .",
    "url": "https://www.a2gov.org/ "
  },
  .....
  {
    "classification": "margin",
    "id": 10,
    "relevance_score": 0.13141067326068878,
    "summary": " A permit is required prior to placing any encroachments on the sidewalk . The Downtown Sidewalk Encroachment Permit Program allows downtown businesses to utilize the sidewalks in front of their businesses for advertising, special events, beautification, and other purposes . All permits need to be submitted through the new project dox portal (link at the top of this page) The City of Bozeman Public Works Department issues two types of permits for events .",
    "url": "https://www.bozeman.net/departments/transportation-engineering/engineering/development-center/permits"
  }
]

```


2. http://127.0.0.1:5000/scraped_links/contact will retrieve all links based on classification: where the highest relevance score is at the top, 
where the classification is anything found in the labels object in config.json 
example:
```
[
  {
    "classification": "contact",
    "id": 11,
    "relevance_score": 0.2438909262418747,
    "summary": " Granicus- Connecting People and Government is a project by Granicus . Granicus is designed to connect people and government .",
    "url": "https://www.bozeman.net/services/online-services"
  }
]
```