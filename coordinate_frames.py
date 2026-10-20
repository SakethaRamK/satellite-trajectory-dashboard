import satellite_orbit
import math
from sgp4.api import jday, Satrec
from datetime import datetime,timezone
satellite_name = "ISS Zarya"
line1 = "1 25544U 98067A   26257.14321681  .00004666  00000+0  92466-4 0  9990"
line2 = "2 25544  51.6309 219.8284 0004931 139.3822 220.7535 15.49107075585545"
earth_radius = 6371
def rotate_z(vector,angle):
    new_vector = []
    new_vector.append(vector[0]*math.cos(angle) - vector[1]*math.sin(angle))
    new_vector.append(vector[0]*math.sin(angle) + vector[1]*math.cos(angle))
    new_vector.append(vector[2])
    return new_vector

def julian_date(time):
    jd, fr = jday(
    time.year,
    time.month,
    time.day,
    time.hour,
    time.minute,
    time.second
    )
    return jd+fr

def gmst(jd):
    time = (jd-2451545.0)/36525
    gmst = 280.46061837 + 360.98564736629*(jd - 2451545.0) + 0.000387933*time*time - pow(time,3)/38710000
    gmst = gmst%360
    return gmst

def teme_to_ecef(vector,time):
    angle_rot = math.radians(gmst(julian_date(time)))
    pos = rotate_z(vector,angle_rot)
    return pos 

def space_pos(ecef_vector):
    mag = satellite_orbit.magnitude(ecef_vector)
    altitude = mag - earth_radius
    longitude = math.degrees(math.atan2(ecef_vector[1],ecef_vector[0]))
    latitude = math.degrees(math.asin(ecef_vector[2]/satellite_orbit.magnitude(ecef_vector)))
    return (altitude,longitude,latitude)   

def main():
    satellite = Satrec.twoline2rv(line1,line2)
    start_time = datetime(2026,9,14,12,0,0,tzinfo=timezone.utc)
    jd, fr = jday(start_time.year,start_time.month,start_time.day,start_time.hour,start_time.minute,start_time.second)
    error, position, velocity = satellite.sgp4(jd,fr)
    if error == 0:
        print(f"TEME position: {position}")
        print(f"Velocity: {velocity}")
        ecef_vector = teme_to_ecef(position,start_time)
        print(f"ECEF position: {ecef_vector}")
        altitude, longitude, latitude = space_pos(ecef_vector)
        print(f"Altitude: {altitude} km")
        print(f"Longitude: {longitude} degrees")
        print(f"Latitude: {latitude} degrees")

if __name__ == "__main__":
    main()