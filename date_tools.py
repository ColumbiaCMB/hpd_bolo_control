import datetime

def dt_to_mjd(dtime):
    mjd_start = datetime.datetime(1858,11,17,0,0)
    x = dtime - mjd_start
    return x.days + (x.seconds + x.microseconds*1e-6)/(60.0*60.0*24.0)

def mjdnow():
    t_date = datetime.datetime.utcnow()
    return dt_to_mjd(t_date)

