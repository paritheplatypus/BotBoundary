# BotBoundary

> In-progress senior capstone project focused on behavioral bot detection during authentication.

## Overview

BotBoundary is a project exploring how behavioral signals during login can be used to help distinguish human users from bots or suspicious activity.

This repository is currently under active development.

## Current Stack

- **Frontend:** React
- **Backend:** Python
- **Hosting:** AWS EC2
- **Database:** DynamoDB
- **Frontend Deployment:** Vercel
- **Tunneling / Demo Access:** ngrok

## Project Status

This project is still in progress. More documentation will be added as development continues.

## Running the Backend

Current backend startup flow:

### On EC2

Start the backend service:

```bash
sudo systemctl start botboundary
```

Expose the backend on port `8000` with ngrok:

```bash
ngrok http 8000
```

## Frontend

Frontend is currently available at:

```text
https://botboundarywebsite.vercel.app/
```
