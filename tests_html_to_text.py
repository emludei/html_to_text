import unittest

from collections import namedtuple

from html_to_text import parser


class TestTag(unittest.TestCase):
    def setUp(self):
        self.tag_name = 'a'
        self.attrs = [('href', 'https://www.google.ru/')]
        self.tag = parser.Tag(self.tag_name, self.attrs)

    def test_starttag_string(self):
        attributes = ' '.join(('{0}="{1}"'.format(name, value) for name, value in self.attrs))
        self.assertEqual(
            self.tag.starttag_string(save_attrs=True),
            '<' + self.tag_name + ' ' + attributes + '>'
        )

    def test_endtag_string(self):
        self.assertEqual(self.tag.endtag_string(), '</' + self.tag_name + '>')

    def test_property_name(self):
        self.assertEqual(self.tag.name, self.tag_name)

    def test_property_attrs(self):
        self.assertEqual(self.tag.attrs, self.attrs)

    def test_property_writed(self):
        self.assertFalse(self.tag.writed)
        self.tag.writed = True
        self.assertTrue(self.tag.writed)

    def test_property_is_start_of_chunk(self):
        self.assertFalse(self.tag.is_start_of_chunk)
        self.tag.is_start_of_chunk = True
        self.assertTrue(self.tag.is_start_of_chunk)

    def test_property_is_start_of_save_chunk(self):
        self.assertFalse(self.tag.is_start_of_save_chunk)
        self.tag.is_start_of_save_chunk = True
        self.assertTrue(self.tag.is_start_of_save_chunk)


class TestChunk(unittest.TestCase):
    def setUp(self):
        self.punctuation = '.,!?:;'
        self.cleaner = parser.HTMLChunksCleaner()
        self.useful_text = 'test paragraph?!'
        self.chunk = '<div><p>{0}</p></div>'.format(self.useful_text)

    def test_calculate_length_with_tags(self):
        chunk = parser.Chunk(self.chunk)
        chunk._calculate_length_with_tags()
        self.assertEqual(chunk.length_with_tags, len(self.chunk))

    def test_calculate_length_without_tags(self):
        chunk = parser.Chunk(self.chunk)

        self.assertRaises(parser.ChunkProcedureException, chunk._calculate_length_without_tags)

        chunk._calculate_length_with_tags()

        self.assertFalse(chunk._cleaned)
        self.assertRaises(parser.ChunkProcedureException, chunk._calculate_length_without_tags)

        chunk._calculate_links_length_and_clean_chunk(self.cleaner)

        self.assertEqual(chunk._links_length, 0)

        chunk._calculate_length_without_tags()

        self.assertEqual(chunk.length_without_tags, len(self.useful_text))

    def test_calculate_count_of_punctuation_marks(self):
        count_of_punctuation_marks = sum((self.chunk.count(mark) for mark in self.punctuation))
        chunk = parser.Chunk(self.chunk)

        self.assertRaises(
            parser.ChunkProcedureException,
            chunk._calculate_count_of_punctuation_marks,
            self.punctuation
        )

        self.assertRaises(
            parser.ChunkProcedureException,
            chunk._calculate_links_length_and_clean_chunk,
            self.cleaner
        )

        chunk._calculate_length_with_tags()
        chunk._calculate_links_length_and_clean_chunk(self.cleaner)
        chunk._calculate_count_of_punctuation_marks(self.punctuation)

        self.assertEqual(chunk.count_of_punctuation_marks, count_of_punctuation_marks)

    def test_calculate_links_length_and_clean_chunk(self):
        chunk = parser.Chunk('<p><a href="#">asd<a href="#">asd</a>asd</a>asd</p>')

        chunk._calculate_length_with_tags()
        chunk._calculate_links_length_and_clean_chunk(self.cleaner)

        self.assertEqual(chunk.chunk, 'asd' * 4)
        self.assertEqual(chunk.length_of_links, 9)

    def test_make_calculations(self):
        chunk = parser.Chunk(self.chunk)
        chunk.make_calculations(self.cleaner, self.punctuation)

        text_density = len(self.useful_text) / len(self.chunk)
        count_of_punctuation_marks = sum((self.chunk.count(mark) for mark in self.punctuation))

        weight = (text_density + count_of_punctuation_marks / 100) + 1
        weight += (1 - count_of_punctuation_marks / len(self.useful_text))

        self.assertEqual(chunk.weight, weight)


class TestCleaner(unittest.TestCase):
    def test_feed(self):
        html = '<p>test <b>par<b>agr<b>aph</b> <span>!<span>asdsadsadas</span></span></p>'
        cleaned_html = '<p>test paragraph </p>'

        cleaner = parser.Cleaner(
            remove_with_data={'span'},
            remove_without_data={'b'}
        )

        cleaner.feed(html)

        self.assertEqual(cleaner.data, cleaned_html)


class TestHTMLChunksCleaner(unittest.TestCase):
    def setUp(self):
        TestData = namedtuple('TestData', ['chunk', 'cleaned_data', 'length_of_links'])

        self.data = (
            TestData('<p>testp</p><a href="#">test link</a>', 'testptest link', 9),
        )

    def test_feed_default_settings(self):
        cleaner = parser.HTMLChunksCleaner()

        for item in self.data:
            cleaner.feed(item.chunk)

            self.assertEqual(cleaner.data, item.cleaned_data)
            self.assertEqual(cleaner.links_length, item.length_of_links)

            cleaner.clear()

            self.assertFalse(bool(cleaner.data))
            self.assertEqual(cleaner.links_length, 0)

    def test_feed_need_calculate_length_false(self):
        cleaner = parser.HTMLChunksCleaner(need_calculate_length=False)

        for item in self.data:
            cleaner.feed(item.chunk)

            self.assertEqual(cleaner.data, item.cleaned_data)
            self.assertEqual(cleaner.links_length, 0)

            cleaner.clear()

            self.assertFalse(bool(cleaner.data))


class TestHTMLSplitter(unittest.TestCase):
    def test_feed(self):
        html = (
            '<html>'
            '<head><title>Test title</title></head>'
            '<body><p><b>test paragraph</b>test paragraph</p><p>test paragraph</p></body>'
            '</html>'
        )

        chunks = [
            '<title>Test title</title>',
            '<b>test paragraph</b>',
            '<p>test paragraph</p>',
            '<p>test paragraph</p>'
        ]

        splitter = parser.HTMLSplitter(
            tag_wrapper=parser.get_tag_wrapper(True, parser.Tag),
            chunks_wrapper=parser.get_chunks_wrapper(parser.Chunk),
            save_chunks_wrapper=parser.get_save_chunks_wrapper()
        )

        splitter.feed(html)

        self.assertEqual([chunk.chunk for chunk in splitter.data], chunks)

        splitter.clear()

        self.assertFalse(bool(splitter.data))

    def test_saving_tags(self):
        html = '<div>asdasd<h1>Test <b>h1</b></h1>asdsad<h2>Test h2</h2>asdasd</div>'

        saved_tags = {
            'h1': ['<h1>Test <b>h1</b></h1>'],
            'h2': ['<h2>Test h2</h2>']
        }

        splitter = parser.HTMLSplitter(
            {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'},
            {'div', 'p'},
            tag_wrapper=parser.get_tag_wrapper(True, parser.Tag),
            chunks_wrapper=parser.get_chunks_wrapper(parser.Chunk),
            save_chunks_wrapper=parser.get_save_chunks_wrapper()
        )

        splitter.feed(html)

        self.assertEqual(splitter.saved_tags, saved_tags)


class TestFunctions(unittest.TestCase):
    def test_normalize_string(self):
        test_data = (
            ' asd    asd   a sdas     das    dasd asd asd as   dasad as a     ',
            'asd asd a sdas das dasd asd asd as dasad as a'
        )

        self.assertEqual(parser.normalize_string(test_data[0]), test_data[1])


if __name__ == '__main__':
    unittest.main()
