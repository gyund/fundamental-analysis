# import os
# import pytest
# from xbrl.cache import HttpCache
# from xbrl.instance import XbrlParser, XbrlInstance


# @pytest.mark.skip(reason="xml has issues with the format")
# def test_xbrl_parsing():
#     dirname = os.path.dirname(__file__)
#     cache_dir = os.path.join(dirname, 'edgar_samples')
#     filename = os.path.join(
#         dirname, 'edgar_samples/aapl/10-K/0000320193-21-000105.txt')

#     cache: HttpCache = HttpCache(cache_dir)
#     parser = XbrlParser(cache)

#     inst: XbrlInstance = parser.parse_instance(filename)
