# NetLearn

An interactive, beginner-friendly networking learning platform. Learn a concept, see it in action, and test yourself, all in one place.

## Features

- Account registration, login and course enrollment
- 6 modules with 3 lessons each, plus a quiz per module
- Unlock flow: lessons open in order, and the next module unlocks after you pass the previous quiz
- Lesson focus mode for distraction-free reading
- Progress dashboard
- Certificate of completion with a public verification page
- Three interactive tools:
  - **Subnet Calculator**: network, broadcast, host range, binary view and subnet splitting
  - **Packet Walk**: step-by-step visualization of how a packet travels through a network
  - **Router CLI Lab**: practice router commands in a simulated CLI

## Tech Stack

- Python, Flask
- SQLite
- Jinja2 templates, HTML, CSS, JavaScript
- NetworkX, Markdown

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000

## Project Structure

```
app/
  content/      lesson Markdown files and quiz JSON for each module
  services/     progress, subnet, routing and CLI simulation logic
  templates/    HTML templates
  static/       CSS and images
  db.py, schema.sql
config.py
run.py
```

## Demo

Demo video: *(add your link here)*

## Author

Created by WL. Chathurika Madhuwanthi, University of Sri Jayewardenepura.
