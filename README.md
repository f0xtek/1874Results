# 1874Results

Serverless function running on AWS Lambda that scrapes the latest result & next fixture for [1874 Northwich](https://1874northwich.com/) Football Club.

The function runs on a cron schedule via [Amazon EventBridge](https://aws.amazon.com/eventbridge/), scrapes the results page to parse the latest result & next fixture, then utilises the [Twillio API](https://www.twilio.com/) to send an SMS to a configured mobile number.

Deployment to AWS Lambda is handled via the [AWS Chalice](https://aws.github.io/chalice/) serverless python framework.
