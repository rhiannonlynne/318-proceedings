def translateEpoch(mpcEpoch):
    import string
    import datetime
    year_a = mpcEpoch[0]
    year_b = int(mpcEpoch[1:3])
    month = mpcEpoch[3]
    day = mpcEpoch[4:6]
    year_ref = {}
    year_ref['I'] = 1800
    year_ref['J'] = 1900
    year_ref['K'] = 2000
    year = year_ref[year_a] + year_b
    try:
        month = int(month)
    except ValueError:
        month = string.uppercase.index(month) + 10
    try:
        day = int(day)
    except ValueError:
        day = string.uppercase.index(day) + 10
    d = datetime.date(year, month, day)
    d2 = datetime.date(1994, 1, 1)
    mjd2 = 49353
    mjd = d.toordinal() - d2.toordinal() + mjd2
    return mjd
