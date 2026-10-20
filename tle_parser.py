def validate(line1,line2):
    if line1[0] != "1" or line2[0] != "2":
        return False
    if len(line1) != 69 or len(line2) != 69:
        return False
    try:
        num1 = int(line1[2:7])
        num2 = int(line2[2:7])
    except ValueError:
        print("Invalid TLE")
        return False
    else:
        if num1 != num2:
            return False
    if (cal_checksum(line1) != int(line1[-1])) or (cal_checksum(line2) != int(line2[-1])):
        return False
    return True

def cal_checksum(line):
    total = 0
    for character in line[:-1]:
        if character.isdigit():
            total += int(character)
        elif character == "-":
            total += 1
        else:
            continue
    return total%10

def sat_data(line1,line2):
    try:
        satellite_id = int(line1[2:7])
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        eccentricity = float("0." + line2[26:33])
        argument_of_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        period = 24/mean_motion
    except ValueError:
        print("Error occurred while retrieving TLE data of the satellite")
    else:
        result = {
            "satellite_id" : satellite_id,
            "inclination" : inclination,
            "raan" : raan,
            "eccentricity" : eccentricity,
            "argument_of_perigee" : argument_of_perigee,
            "mean_anomaly" : mean_anomaly,
            "mean_motion" : mean_motion,
            "period" : period
        }
        return result

def main():
    line1 = "1 25544U 98067A   26257.14321681  .00004666  00000+0  92466-4 0  9990"
    line2 = "2 25544  51.6309 219.8284 0004931 139.3822 220.7535 15.49107075585545"
    if validate(line1,line2):
        print("TLE validation: Valid")
        data = sat_data(line1,line2)
        print(f"Satellite ID: {data["satellite_id"]}")
        print(f"Inclination: {data["inclination"]} degrees")
        print(f"RAAN: {data["raan"]} degrees")
        print(f"Eccentricity: {data["eccentricity"]}")
        print(f"Argument of perigee: {data["argument_of_perigee"]} degrees")
        print(f"Mean Anomaly: {data["mean_anomaly"]} degrees")
        print(f"Mean Motion: {data["mean_motion"]} rotations per day")
        print(f"Orbit period: {round(data["period"],3)} hours")
    else:
        print("TLE validation: Invalid")

if __name__ == "__main__":
    main()