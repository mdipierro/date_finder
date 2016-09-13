# date_finder

A program that finds and normalizes dates in arbitrary strings and most standard formats

Example:

    >>> from date_finder import DateFinder
    >>> text = "I will arrive on Jan 1st and depart on 6/12/2015"
    >>> finder = DateFinder()
    >>> finder.find_dates(text)
    [((17, 24), 'Jan 1st', datetime.date(2016, 1, 1)), ((39, 48), '6/12/2015', datetime.date(2015, 6, 12))]
    >>> finder.normalize_dates('%Y.%m.%d')
    "I will arrive on 2016.01.01 and depart on 2016.06.12"
