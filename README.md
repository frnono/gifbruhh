<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copy Code Example</title>
    <style>
        .code-container {
            position: relative;
            margin: 1em 0;
            padding: 0.5em;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
        }
        .copy-button {
            position: absolute;
            top: 0.5em;
            right: 0.5em;
            padding: 0.2em 0.5em;
            background-color: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="code-container">
        <button class="copy-button" onclick="copyCode()">Copy</button>
        <pre><code id="code">pyinstaller --onefile --windowed --icon=E:/Pictures/icons/asriel.ico --add-data "asriel.ico;." gifbruhh.py</code></pre>
    </div>

    <script>
        function copyCode() {
            const code = document.getElementById("code").textContent;
            navigator.clipboard.writeText(code).then(() => {
                alert("Code copied to clipboard!");
            }).catch(err => {
                console.error("Failed to copy: ", err);
            });
        }
    </script>
</body>
</html>
