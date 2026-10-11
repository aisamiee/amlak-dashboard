"""Gregorian -> Jalali (Solar Hijri) conversion, no dependencies."""
import datetime

MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
          'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def g2j(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def today_jalali(dt=None):
    dt = dt or datetime.datetime.now()
    return g2j(dt.year, dt.month, dt.day)


def today_str(dt=None):
    """'1405/07/17'"""
    y, m, d = today_jalali(dt)
    return f'{y}/{m:02d}/{d:02d}'


def today_fa(dt=None):
    """'۱۷ مهر ۱۴۰۵'"""
    y, m, d = today_jalali(dt)
    return f'{d} {MONTHS[m - 1]} {y}'.translate(FA_DIGITS)


if __name__ == '__main__':
    assert g2j(2026, 10, 9) == (1405, 7, 17), g2j(2026, 10, 9)
    assert g2j(2026, 3, 21) == (1405, 1, 1), g2j(2026, 3, 21)
    print(today_str(), today_fa())
