#!/usr/bin/env python3
"""
HTML fixtures for MockExecutor to simulate realistic web content.
"""

# HTML fixtures for different test scenarios
HTML_FIXTURES = {
    "simple_click": """
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
  <h1>Test Page</h1>
  <button id="btn1">Click me</button>
  <div id="output"></div>
  <a href="/page2">Next Page</a>
</body>
</html>
""",
    "form_fill": """
<!DOCTYPE html>
<html>
<head><title>Contact Form</title></head>
<body>
  <form id="contact">
    <input type="text" id="name" placeholder="Name">
    <input type="email" id="email" placeholder="Email">
    <textarea id="message" placeholder="Message"></textarea>
    <button type="submit">Submit</button>
  </form>
</body>
</html>
""",
    "multi_page": """
<!DOCTYPE html>
<html>
<head><title>Page 1</title></head>
<body>
  <nav>Page 1</nav>
  <a href="/page2">Go to Page 2</a>
  <table id="data">
    <tr><th>Name</th><th>Value</th></tr>
    <tr><td>A</td><td>100</td></tr>
    <tr><td>B</td><td>200</td></tr>
  </table>
</body>
</html>
""",
    "page2": """
<!DOCTYPE html>
<html>
<head><title>Page 2</title></head>
<body>
  <nav>Page 2</nav>
  <a href="/page1">Back to Page 1</a>
  <div id="result">Success!</div>
</body>
</html>
""",
    "page3": """
<!DOCTYPE html>
<html>
<head><title>Page 3 - Download</title></head>
<body>
  <h1>Download Center</h1>
  <a href="/download/report.pdf" download>Download Report</a>
  <ul id="files">
    <li>report.pdf</li>
    <li>data.csv</li>
  </ul>
</body>
</html>
"""
}
