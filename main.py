import os
import json
from quart import Quart, request, Response, render_template, redirect, url_for

app = Quart(__name__, static_url_path="/static", static_folder="static")


print("Online")

def file_type(filename):
    """Determine the type of a given file or directory."""
    if os.path.isdir(filename):
        return "Directory"
    elif os.path.isfile(filename):
        return "File"
    else:
        return "Unknown"

def format_file_size(size_in_bytes):
    """Convert file size in bytes to a human-readable format (KB, MB, GB, etc.)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"

def get_directory_stats(directory):
    """Calculate the total size, number of files, and file details in a directory."""
    total_size = 0
    num_files = 0
    files = []
    for root, dirs, filenames in os.walk(directory):
        for name in filenames:
            filepath = os.path.join(root, name)
            file_size = os.path.getsize(filepath)
            total_size += file_size
            num_files += 1
            files.append({
                "name": name,
                "size": file_size,
                "formatted_size": format_file_size(file_size)
            })
    return {
        "total_size": total_size,
        "formatted_total_size": format_file_size(total_size),
        "num_files": num_files,
        "files": files
    }

def update_files_json():
    """Update the files.json file with the latest stats from the /static/ directory."""
    stats = get_directory_stats(app.static_folder)
    with open("files.json", "w") as f:
        json.dump(stats, f, indent=4)

@app.route("/")
async def index() -> str:
    """Render the homepage with file stats and a list of files."""
    update_files_json()
    with open("files.json", "r") as f:
        files_data = json.load(f)
    return await render_template(
        "index.html",
        num_files=files_data["num_files"],
        total_size=files_data["formatted_total_size"],
        files=files_data["files"]
    )

@app.route("/upload", methods=["GET", "POST"])
async def upload_file():
    """Handle file uploads."""
    if request.method == "POST":
        files = await request.files 
        uploaded_file = files.get("file")
        if uploaded_file:
            if not os.path.exists(app.static_folder):
                os.makedirs(app.static_folder)
            file_path = os.path.join(app.static_folder, uploaded_file.filename)
            await uploaded_file.save(file_path)
            update_files_json()
            return redirect(url_for("index")) 
    return await render_template("upload.html")


@app.route("/static/<name>")
async def get_static_file(name: str) -> Response:
    """Serve static files from the /static/ directory."""
    file_path = os.path.join(app.static_folder, name)
    if os.path.exists(file_path):
        with open(file_path, "rb") as file_data:
            return Response(file_data.read(), mimetype="application/octet-stream")
    else:
        return Response("File not found", status=404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="25580")
