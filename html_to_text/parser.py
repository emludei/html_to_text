from html import parser


__all__ = [
    'normalize_string',
    'get_tag_wrapper',
    'get_html_chunks_cleaner',
    'get_html_cleaner',
    'get_save_html_chunks_cleaner',
    'get_chunks_wrapper',
    'get_save_chunks_wrapper',
    'get_html_splitter',
    'get_parser'
]


class ChunkProcedureException(Exception):
    pass


class Tag:
    """Creates new tag object with given parameters.

    Args:
        name: Name of tag.
        attrs: List of attributes. -> [('href', 'https://www.google.ru/'), ...] (example for tag <a>)

    Returns:
        Tag object.

        Tag(name='a', [('href', 'https://www.google.ru/')]) -> tag

    Methods defined here:
        starttag_string(self, save_attrs=False)
            Return a string representation of opened tag with attributes, if parameter save_attrs is True,
            and without attributes in another case.

        endtag_string(self)
            Return a string representation of closed tag.

    Properties:
        name: Return name of tag.
        attrs: Return attrs.
        writed: Return True - if the tag is already recorded in a certain Chunk (html block).
            False in another case.
        is_start_of_chunk: Return True - if the tag is start of a certain Chunk. False in another case.
        is_start_of_save_chunk: Return True - if the tag is start of a certain 'save' Chunk.
            False in another case.
    """
    __slots__ = (
        '_name',
        '_attrs',
        '_writed',
        '_is_start_of_chunk',
        '_is_start_of_save_chunk'
    )

    def __init__(self, name, attrs):
        self._name = name
        self._attrs = attrs

        self._writed = False
        self._is_start_of_chunk = False
        self._is_start_of_save_chunk = False

    def starttag_string(self, save_attrs=False):
        """Generates and returns opening tag string.

        Args:
            save_attrs: If parameter is true, attributes of tag will be save, default False.

        Returns:
            A string representation of opened tag with attributes, if parameter save_attrs is True,
            and without attributes in another case.


            1) <tag attr1="value" attr2="value">
            2) <tag>
        """

        return get_starttag_string(self.name, self.attrs, save_attrs)

    def endtag_string(self):
        """Generates and returns closing tag string.

        Returns:
            A string representation of closed tag.

            </tag>
        """
        return get_endtag_string(self.name)

    @property
    def name(self):
        return self._name

    @property
    def attrs(self):
        return self._attrs

    @property
    def writed(self):
        return self._writed

    @writed.setter
    def writed(self, value):
        if not isinstance(value, bool):
            raise AttributeError('Type of value must be boolean')

        self._writed = value

    @property
    def is_start_of_chunk(self):
        return self._is_start_of_chunk

    @is_start_of_chunk.setter
    def is_start_of_chunk(self, value):
        if not isinstance(value, bool):
            raise AttributeError('Type of value must be boolean')

        self._is_start_of_chunk = value

    @property
    def is_start_of_save_chunk(self):
        return self._is_start_of_save_chunk

    @is_start_of_save_chunk.setter
    def is_start_of_save_chunk(self, value):
        if not isinstance(value, bool):
            raise AttributeError('Type of value must be boolean')

        self._is_start_of_save_chunk = value


class Chunk:
    """Creates block with html.

    Args:
        chunk: Block with html code.

    Returns:
        A chunk object.
        Chunk('<div class='content'><p>Test</p></div>') -> chunk

    Methods defined here:
        make_calculations(self, cleaner, punctuation):
            Calculate weight of this chunk. The greater the weight,
            the greater the likelihood that the block contains useful text.

    Properties:
        chunk: Return chunk (string).
        weight: Return weight of the chunk.
        length_with_tags: Return length with html tags of the chunk.
        length_without_tags: Return length without html tags of the chunk.
        length_of_links: Return length of links in chunk.
        count_of_punctuation_marks: Return number of punctuation marks contained by chunk.
    """
    __slots__ = (
        '_chunk',
        '_weight',
        '_length_with_tags',
        '_length_without_tags',
        '_count_of_punctuation_marks',
        '_links_length',
        '_cleaned'
    )

    def __init__(self, chunk=''):
        self._chunk = chunk

        self._weight = 0
        self._length_with_tags = 0
        self._length_without_tags = 0
        self._count_of_punctuation_marks = 0
        self._links_length = 0

        self._cleaned = False

    def make_calculations(self, cleaner, punctuation):
        """Calculates weight of the chunk.

        Args:
            cleaner: Object which have method 'feed(data)', removes tags from chunk
                and calculate length of links in the chunk.
            punctuation: Punctuation marks.
        """
        self._calculate_length_with_tags()
        self._calculate_links_length_and_clean_chunk(cleaner)
        self._calculate_length_without_tags()
        self._calculate_count_of_punctuation_marks(punctuation)

        text_density = self._length_without_tags / self._length_with_tags
        links_density = self._links_length / max(self._length_without_tags, 1)

        self._weight = (text_density + self._count_of_punctuation_marks / 100) + (1 - links_density)
        self._weight += (1 - (self._count_of_punctuation_marks / self._length_without_tags))

        if self._count_of_punctuation_marks == 0:
            self._weight *= self._count_of_punctuation_marks

    def _calculate_length_with_tags(self):
        if self._length_without_tags > 0:
            raise ChunkProcedureException(
                'Parameter length_with_tags must be calculated before length_without_tags'
            )

        self._length_with_tags = len(self._chunk)

    def _calculate_length_without_tags(self):
        if self._length_with_tags == 0 or not self._cleaned:
            raise ChunkProcedureException(
                'Parameter length_without_tags must be calculated after length_with_tags '
                'and after removing tags from chunk'
            )

        self._length_without_tags = len(self._chunk)

    def _calculate_count_of_punctuation_marks(self, punctuation):
        if not self._cleaned:
            raise ChunkProcedureException(
                'Parameter count_of_punctuation_marks must be calculated after removing tags from chunk'
            )

        self._count_of_punctuation_marks = sum([self._chunk.count(mark) for mark in punctuation])

    def _calculate_links_length_and_clean_chunk(self, cleaner):
        if self._length_with_tags == 0:
            raise ChunkProcedureException(
                'Method must be call only after calculating a length_with_tag parameter'
            )

        cleaner.feed(self._chunk)

        self._cleaned = True
        self._links_length = cleaner.links_length
        self._chunk = cleaner.data

    @property
    def chunk(self):
        return self._chunk

    @property
    def weight(self):
        return self._weight

    @property
    def length_with_tags(self):
        return self._length_with_tags

    @property
    def length_without_tags(self):
        return self._length_without_tags

    @property
    def length_of_links(self):
        return self._links_length

    @property
    def count_of_punctuation_marks(self):
        return self._count_of_punctuation_marks


class Cleaner(parser.HTMLParser):
    """Creates object for remove tags from html documents

    Args:
        remove_without_data: A set of tags which will be removed without their content.
        remove_with_data: A set of tags which will be removed with content.
        convert_charrefs: If it is True, all character references are
            automatically converted to the corresponding Unicode characters.

    Returns:
        Cleaner object.
    """
    first_run = False

    def __init__(self, remove_without_data=set(), remove_with_data=set(), convert_charrefs=True):
        self._remove_without_data = remove_without_data
        self._remove_with_data = remove_with_data

        self._remove = 0

        self._data = []

        super(Cleaner, self).__init__(convert_charrefs=convert_charrefs)

    def feed(self, data):
        if not self.first_run:
            self.first_run = True
        else:
            self.clear()

        super(Cleaner, self).feed(data)

    def handle_starttag(self, name, attrs):
        if name in self._remove_with_data:
            self._remove += 1

        if name not in self._remove_without_data and self._remove == 0:
            self._data.append(get_starttag_string(name, attrs))

    def handle_endtag(self, name):
        if name not in self._remove_without_data and self._remove == 0:
            self._data.append(get_endtag_string(name))

        if name in self._remove_with_data:
            self._remove -= 1

    def handle_data(self, data):
        if self._remove == 0:
            self._data.append(data)

    def clear(self):
        self._remove = 0
        self._data.clear()

    @property
    def data(self):
        return ''.join(self._data)


class HTMLChunksCleaner(parser.HTMLParser):
    """Creates object that can remove html tags from chunks
    and calculate length of links in the chunk if needed

    Usage:
        cleaner = HTMLChunksCleaner()
        cleaner.feed(data)

    Args:
        tag_link: Tag link.
        need_calculate_length: It identifies the need to calculate length of links

    Returns:
        HTMLChunksCleaner object.

        HTMLChunksCleaner(tag_link='a', need_calculate_length=False) -> html cleaner

    Methods defined here:
        feed(self, data)
            Feed data to the cleaner.

        clear(self)
            Reset this instance.

    Properties:
        data: Return cleaned data.
        links_length: Return length of links.
        tag_link: Return tag link.
    """
    _first_run = False

    def __init__(self, tag_link='a', need_calculate_length=True):
        self._tag_link = tag_link
        self._need_calculate_length = need_calculate_length

        self._links_length = 0
        self._calculate_links_length = 0

        self._data = []

        super(HTMLChunksCleaner, self).__init__(convert_charrefs=True)

    def feed(self, data):
        if self._first_run:
            self.clear()
        else:
            self._first_run = True

        super(HTMLChunksCleaner, self).feed(data)

    def handle_starttag(self, name, attrs):
        if self._need_calculate_length and name == self._tag_link:
            self._calculate_links_length += 1

    def handle_endtag(self, name):
        if self._need_calculate_length and name == self._tag_link:
            self._calculate_links_length -= 1

    def handle_data(self, data):
        if self._need_calculate_length and self._calculate_links_length > 0:
            self._links_length += len(data)

        self._data.append(data)

    def clear(self):
        self._links_length = 0
        self._calculate_links_length = 0
        self._data.clear()

    @property
    def data(self):
        return ''.join(self._data)

    @property
    def links_length(self):
        return self._links_length

    @property
    def tag_link(self):
        return self._tag_link

    @tag_link.setter
    def tag_link(self, value):
        if not isinstance(value, str):
            raise TypeError('This parameter can only be a str type')

        self._tag_link = value


class HTMLSplitter(parser.HTMLParser):
    """Creates object that can split html document on little blocks.

    Usage:
        splitter = HTMLSplitter(
            tags_to_save={'title'},
            tags_to_remove={'head', 'script', 'style', 'pre', 'code'},
            tag_wrapper=get_tag_wrapper(...),
            cunks_wrapper=get_chunks_wrapper(...),
            save_chunks_wrapper=get_save_chunks_wrapper(...)
        )
        splitter.feed(html)

    Args:
        tags_to_save: A set of tags for saving.
        tags_to_remove: A set of tags for removing.
        tag_wrapper: A wrapper for tags.
        chunks_wrapper: A wrapper for html blocks.
        save_chunks_wrapper: A wrapper for tags from 'tags_to_save' set.

    Returns:
        HTMLSplitter object.

    Methods defined here:
        feed(self, data)
            Feed html document to splitter.

        clear(self)
            Reset parser instance.

    Properties:
        data: Return list of chunks (html blocks).
        saved_tags: Return saved tags (which contained by 'tags_to_save' set).
        chunks_wrapper: Return chunks wrapper.
        save_chunks_wrapper: Return 'save' chunks wrapper.
    """
    _first_run = False

    def __init__(self, tags_to_save=set(), tags_to_remove=set(), tag_wrapper=None, chunks_wrapper=None,
                 save_chunks_wrapper=None):
        self._tags_to_save = tags_to_save
        self._tags_to_remove = tags_to_remove

        # wrappers
        self._tag_wrapper = tag_wrapper
        self._chunks = chunks_wrapper
        self._save_chunks = save_chunks_wrapper

        # parameters needed in parsing process
        self._opened_tags = []
        self._save = 0
        self._remove = 0
        self._temp_chunk = []
        self._chunk_started = False

        self._temp_save_chuck = []
        self._save_chunk_started = False

        super(HTMLSplitter, self).__init__(convert_charrefs=True)

    def feed(self, data):
        if self._first_run:
            self.clear()
        else:
            self._first_run = True

        super(HTMLSplitter, self).feed(data)

    def handle_starttag(self, name, attrs):
        tag = self._tag_wrapper.create(name, attrs)

        self._opened_tags.append(tag)

        if name in self._tags_to_save:
            self._save += 1
        if name in self._tags_to_remove:
            self._remove += 1

        if self._remove == 0 and self._chunk_started:
            self._temp_chunk.append(self._tag_wrapper.starttag_string(tag))
            tag.writed = True

        if self._save > 0:
            self._temp_save_chuck.append(self._tag_wrapper.starttag_string(tag))
            tag.writed = True

            if not self._save_chunk_started and name in self._tags_to_save:
                tag.is_start_of_save_chunk = True
                self._save_chunk_started = True

    def handle_endtag(self, name):
        tag = self._opened_tags.pop(-1)

        if self._remove == 0:
            if self._temp_chunk:
                self._temp_chunk.append(self._tag_wrapper.endtag_string(tag))

            if tag.is_start_of_chunk and name == tag.name:
                self._create_chunk_and_reset()

        if self._save > 0:
            self._temp_save_chuck.append(self._tag_wrapper.endtag_string(tag))

        if tag.is_start_of_save_chunk and name == tag.name:
            self._create_save_chunk_and_reset(tag.name)

        if name in self._tags_to_save:
            self._save -= 1
        if name in self._tags_to_remove:
            self._remove -= 1

    def handle_data(self, data):
        if not data.isspace():
            tag = self ._opened_tags[-1]

            if self._remove == 0:
                if not self._chunk_started:
                    tag.is_start_of_chunk = True
                    self._chunk_started = True

                if self._chunk_started:
                    self._add_data_to_chunk(data, tag)

            if self._save > 0:
                self._temp_save_chuck.append(data)

    def _add_data_to_chunk(self, data, tag):
        if not tag.writed:
            self._temp_chunk.append(self._tag_wrapper.starttag_string(tag))
            tag.writed = True

        self._temp_chunk.append(data)

    def _create_chunk_and_reset(self):
        self._chunks.create(''.join(self._temp_chunk))
        self._temp_chunk.clear()
        self._chunk_started = False

    def _create_save_chunk_and_reset(self, tag_name):
        self._save_chunks.create(''.join(self._temp_save_chuck), tag_name)
        self._temp_save_chuck.clear()
        self._save_chunk_started = False

    def clear(self):
        self._chunks.clear()
        self._save_chunks.clear()

        self._opened_tags.clear()
        self._temp_chunk.clear()
        self._temp_save_chuck.clear()

        self._save = 0
        self._remove = 0

        self._chunk_started = False
        self._save_chunk_started = False

    @property
    def data(self):
        return self._chunks.data

    @property
    def saved_tags(self):
        return self._save_chunks.data

    @property
    def chunks_wrapper(self):
        return self._chunks

    @property
    def save_chunks_wrapper(self):
        return self._save_chunks


class Parser:
    """Creates object for extracting useful text information from html documents.

    Usage:
        parser = Parser(
            splitter=splitter,
            chunks_wrapper=chunks_wrapper,
            save_chunks_wrapper=save_chunks_wrapper,
            min_allowed_weight=2.3
        )


    Args:
        splitter: HTMLSplitter object.
        chunks_cleaner: HTMLChunksCleaner object with need_calculate_length=True.
        save_chunks_cleaner: HTMLChunksCleaner object with need_calculate_length=False.
        punctuation: Punctuation marks.
        min_allowed_weight: Minimum allowed weight for chunk (html block). It needed for
            filtering chunks with useful information.

    Methods defined here:
        feed(self, data)
            Feed html document to parser.

    Returns:
        Parser object.

    Properties:
        data: Return useful text.
        saved_tags: Return saved tags and text contained in these tags ({'title': ['Test title', ...]}).
    """
    def __init__(self, splitter=None, chunks_cleaner=None, save_chunks_cleaner=None,
                 punctuation='.,!?:;', min_allowed_weight=0.0):
        self._splitter = splitter
        self._chunks_cleaner = chunks_cleaner
        self._save_chunks_cleaner = save_chunks_cleaner
        self._punctuation = punctuation
        self._min_allowed_weight = min_allowed_weight

    def feed(self, html_document):
        self._splitter.feed(html_document)
        self._splitter.chunks_wrapper.calculate_weights(self._chunks_cleaner, self._punctuation)
        self._splitter.save_chunks_wrapper.remove_tags(self._save_chunks_cleaner)

    @property
    def data(self):
        useful_chunks = (
            chunk.chunk.strip() for chunk in self._splitter.data
            if chunk.weight >= self._min_allowed_weight
        )

        return ' '.join(useful_chunks)

    @property
    def saved_tags(self):
        return self._splitter.saved_tags


def normalize_string(string):
    """Removes excess spaces from string.

    Returns:
        String without excess spaces.
    """
    if not string:
        return ''

    return ' '.join(string.split())


def get_starttag_string(name, attrs, save_attrs=True):
    """Returns string representation of start tag.

    Args:
        name: Name of tag.
        attrs: Attributes of tag -> ((attr1, value), ...).
        save_attrs: If it is True, attributes of tag will be save.
    """
    tag_content = [name]

    if save_attrs:
        tag_content += ['{0}="{1}"'.format(attr, value) for attr, value in attrs]

    return '<' + ' '.join(tag_content) + '>'


def get_endtag_string(name):
    """Returns string representation of end tag

    Args:
        name: Name of tag.
    """
    return '</' + name + '>'


def get_tag_wrapper(save_attrs, tag_class):
    """Creates and returns wrapper for tags

    Args:
        save_attrs: If parameter is true, attributes of tag will be save, default False.
        tag_class: Tag class.

    Returns
        Wrapper for tags.
    """
    class Wrapper:
        def __init__(self):
            self._tag = tag_class
            self._save_attrs = save_attrs

        def starttag_string(self, tag):
            return tag.starttag_string(save_attrs=self._save_attrs)

        def endtag_string(self, tag):
            return tag.endtag_string()

        def create(self, name, attrs):
            return self._tag(name, attrs)

    return Wrapper()


def get_html_chunks_cleaner(tag_link):
    """Creates and returns HTMLChunksCleaner instance for removing tags from chunks and calculating length of links.

    Args:
        tag_link: Tag link.

    Returns:
        HTMLChunksCleaner instance.
    """
    return HTMLChunksCleaner(tag_link=tag_link)


def get_html_cleaner(remove_without_content=set(), remove_with_content=set(), convert_charrefs=True):
    return Cleaner(
        remove_without_data=remove_without_content,
        remove_with_data=remove_with_content,
        convert_charrefs=convert_charrefs
    )


def get_save_html_chunks_cleaner():
    """Creates and returns HTMLChunksCleaner instance for removing tags from chunks.

    Returns:
        HTMLChunksCleaner instance.
    """
    return HTMLChunksCleaner(need_calculate_length=False)


def get_chunks_wrapper(chunk_class):
    """Creates and returns wrapper for html chunks.

    Args:
        chunk_class: Chunk class.

    Returns:
        Wrapper for html chunks.
    """
    class Wrapper:
        def __init__(self):
            self._chunk_class = chunk_class
            self._chunks = []

        def create(self, chunk):
            self._chunks.append(self._chunk_class(chunk=normalize_string(chunk)))

        def clear(self):
            self._chunks.clear()

        def calculate_weights(self, cleaner, punctuation):
            for chunk in self._chunks:
                chunk.make_calculations(cleaner, punctuation)

        @property
        def data(self):
            return self._chunks

    return Wrapper()


def get_save_chunks_wrapper():
    """Creates and returns wrapper for 'save' chunks."""
    class Wrapper:
        def __init__(self):
            self._save_chunks = {}

        def create(self, chunk, tag_name):
            if tag_name not in self._save_chunks:
                self._save_chunks.update({tag_name: [normalize_string(chunk)]})
            else:
                self._save_chunks[tag_name].append(normalize_string(chunk))

        def remove_tags(self, cleaner):
            for tag in self._save_chunks:
                index = 0
                last_index = len(self._save_chunks[tag])

                while index < last_index:
                    cleaner.feed(self._save_chunks[tag][index])

                    if not cleaner.data:
                        self._save_chunks[tag].pop(index)
                        last_index -= 1
                    else:
                        self._save_chunks[tag][index] = cleaner.data
                        index += 1

        def clear(self):
            self._save_chunks.clear()

        @property
        def data(self):
            return self._save_chunks

    return Wrapper()


def get_html_splitter(tags_to_save, tags_to_remove, tag_wrapper, chunks_wrapper, save_chunks_wrapper):
    """Creates and returns HTMLSplitter instance.

    Args:
        tags_to_save: A set of tags for saving. (for example tag <title>,
            which located in tag for removing - <head>).
        tags_to_remove: A set of tags for removing.
        tag_wrapper: A wrapper for tag objects.
        chunks_wrapper: A wrapper for html chunk objects.
        save_chunks_wrapper: A wrapper for data of tags from 'tags_to_save' set.

    Returns:
        HTMLSplitter instance with given attributes.
    """
    html_splitter = HTMLSplitter(
        tags_to_remove=tags_to_remove,
        tags_to_save=tags_to_save,
        tag_wrapper=tag_wrapper,
        chunks_wrapper=chunks_wrapper,
        save_chunks_wrapper=save_chunks_wrapper
    )

    return html_splitter


def get_parser(tags_to_save, tags_to_remove, punctuation='.,!?:;', min_allowed_weight=0.0, save_attrs=False,
               tag_class=Tag, tag_link='a', chunk_class=Chunk, tag_wrapper=None, chunks_wrapper=None,
               save_chunks_wrapper=None, splitter=None, chunks_cleaner=None, save_chunks_cleaner=None):
    """Creates and returns parser which can extract useful text from html documents.

    Usage:
        parser = get_parser(**kwargs)
        parser.feed(html)

    Args:
        tags_to_save: A set of tags for saving.
        tags_to_remove: A set of tags for removing.
        punctuation: Punctuation marks.
        min_allowed_weight: Minimum allowed weight for chunk (html block).
        save_attrs: If parameter is true, attributes of tag will be save, default False.
        tag_class: Tag class.
        tag_link: Tag link ('a' default).
        chunk_class: Chunk class.
        tag_wrapper: Wrapper for tags.
        chunks_wrapper: Wrapper for chunks (blocks with html).
        save_chunks_wrapper: Wrapper for 'save' chunks.
        splitter: HTMLSplitter instance. Which can split html document to chunks (little blocks with html).
        chunks_cleaner: HTMLChunksCleaner instance. Which can remove tags from chunks and calculate length of links.
        save_chunks_cleaner: HTMLChunksCleaner instance. Which can remove tags from chunks.

    Returns:
        Parser object.

    """
    if splitter is None:
        if tag_wrapper is None:
            tag_wrapper = get_tag_wrapper(save_attrs, tag_class)

        if chunks_wrapper is None:
            chunks_wrapper = get_chunks_wrapper(chunk_class)

        if save_chunks_wrapper is None:
            save_chunks_wrapper = get_save_chunks_wrapper()

        splitter = get_html_splitter(
            tags_to_save=tags_to_save,
            tags_to_remove=tags_to_remove,
            tag_wrapper=tag_wrapper,
            chunks_wrapper=chunks_wrapper,
            save_chunks_wrapper=save_chunks_wrapper
        )

    if chunks_cleaner is None:
        chunks_cleaner = get_html_chunks_cleaner(tag_link)

    if save_chunks_cleaner is None:
        save_chunks_cleaner = get_save_html_chunks_cleaner()

    parser = Parser(
        splitter=splitter,
        chunks_cleaner=chunks_cleaner,
        save_chunks_cleaner=save_chunks_cleaner,
        punctuation=punctuation,
        min_allowed_weight=min_allowed_weight
    )

    return parser
