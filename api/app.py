import sqlite3
from flask import Flask, jsonify
from config.config_loader import load_config

config = load_config()
dbName = config["database"]
app = Flask(__name__)

# Function to retrieve saved links from SQLite DB
def get_saved_links(db_name=dbName):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM links')
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to a more readable format (list of dictionaries)
    links = []
    for row in rows:
        link = {
            'id': row[0],
            'url': row[1],
            'text': row[2],
            'href': row[3],
            'classification': row[4],
            'score': row[5]
        }
        links.append(link)
    
    return links

# Route to get all the scraped and filtered links
@app.route('/scraped_links', methods=['GET'])
def get_links():
    links = get_saved_links()
    return jsonify(links)


# Route to get scraped links by classification (e.g., "contact")
@app.route('/scraped_links/<classification>', methods=['GET'])
def get_links_by_classification(classification):
    links = get_saved_links()
    filtered_links = [link for link in links if link['classification'] == classification]
    return jsonify(filtered_links)

# Starting the Flask app
def main():
    app.run(debug=True)

if __name__ == "__main__":
    main()
