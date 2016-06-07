# html_to_text
This simple library helps you to extract useful text information from html documents.

## Installing

To install html_to_text, simply:
```
pip install html_to_text
```

## Usage:
Prepare your html document and remove exess tags from it. To do this, you can use `html_cleaner` object returned by `get_html_cleaner` function. The `get_html_cleaner` function takes three parameters:
- `remove_without_content`: A set of tags which will be removed  without their content.
- `remove_with_content`: A set of tags which will be removed with their content.
- `convert_charrefs`: If it is True, all character references will be automatically converted to the corresponding Unicode characters (default True).

```python
>>> from html_to_text import get_html_cleaner
>>> html = """
...   <html>
...       <head>
...           <title>Example</title>
...           <script>Some scripts</script>
...           <style>Some style</style>
...       </head>
...       <body>
...           <div class="content">
...               <h1>This is h1 example.</h1>
...               <p><b>This</b> is <b><s>some</s> text<b> information. This is some <span>text</span> 
...               information.</p>
...               <h2>This is h2 example.</h2>
...               <p>This is some text information. This is some text information.</p>
...           </div>
...           <div class="nav">
...               <ul>
...                   <li><a href="#">page 1</a></li>
...                   <li><a href="#">page 2</a></li>
...                   <li><a href="#">page 3</a></li>
...               </ul>
...           </div>
...       </body>
...   </html>
... """
...
>>> cleaner = get_html_cleaner(
...   remove_without_content={'b', 's', 'span'},
...   remove_with_content={'style', 'script'}
... )
...
>>> cleaner.feed(html)
>>> print(cleaner.data)
<html>
  <head>
    <title>Example</title>
    
    
  </head>
  <body>
    <div class="content">
      <h1>This is h1 example</h1>
      <p>This is some text information. This is some text information.</p>
      <h2>This is h2 example</h2>
      <p>This is some text inforamtion. This is some text information.</p>
    </div>
    <div class="nav">
      <ul>
        <li><a href="#">page 1</a></li>
        <li><a href="#">page 2</a></li>
        <li><a href="#">page 3</a></li>
      </ul>
    </div>
  </body>
</html>
```

To extract useful text from html document should use `parser` object returned by `get_parser` function. This function takes:
- `tags_to_save`: A set of tags for saving.
- `tags_to_remove`: A set of tags for removing.
- `punctuation`: Punctuation marks.
- `min_allowed_weight`: Minimum allowed weight for chunk (html block).
- `save_attrs`: If parameter is true, attributes of tag will be save, default False.
- `tag_class`: Tag class.
- `tag_link`: Tag link ('a' default).
- `chunk_class`: Chunk class.
- `tag_wrapper`: Wrapper for tags.
- `chunks_wrapper`: Wrapper for chunks (blocks with html).
- `save_chunks_wrapper`: Wrapper for 'save' chunks.
- `splitter`: HTMLSplitter instance. Which can split html document to chunks (little blocks with html).
- `chunks_cleaner`: HTMLChunksCleaner instance. Which can remove tags from chunks and calculate length of links.
- `save_chunks_cleaner`: HTMLChunksCleaner instance. Which can remove tags from chunks.

```python
>>> from html_to_text import get_parser
>>> parser = get_parser(
...   tags_to_save={'title', 'h1','h2'},
...   tags_to_remove={'h1', 'h2', 'script', 'style'},
...   min_allowed_weight=2.3
... )
...
>>> parser.feed(cleaner.data)
>>> print(parser.data)
This is some text information. This is some text information. This is some text information. This is 
some text information.
>>> print(parser.saved_tags)
{'h1': ['This is h1 example.'], 'title': ['Example'], 'h2': ['This is h2 example.']}
```
