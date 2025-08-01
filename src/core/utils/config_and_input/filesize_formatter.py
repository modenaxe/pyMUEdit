import os


def filesize_formatter(filename: str):
    # Get filsize
    file_size = os.path.getsize(filename)

    # Format file size for display
    if file_size < 1024:
        return f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        return f"{file_size/1024:.1f} KB"
    else:
        return f"{file_size/(1024*1024):.1f} MB"
