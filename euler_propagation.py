import satellite_orbit
import math
distances = []
ideal_orbit = 7000
def euler_step(r,v,dt):
    Rnew = []
    Vnew = []
    acc = satellite_orbit.grav_acc(r)
    for i in range(len(r)):
        Rnew.append(r[i]+v[i]*dt)
        Vnew.append(v[i]+acc[i]*dt)
    distances.append(math.sqrt(Rnew[0]**2 + Rnew[1]**2 + Rnew[2]**2))
    return (Rnew,Vnew)

def euler_propagate(r,v,dt,step):
    trajectory = []
    new_position = r
    new_velocity = v
    trajectory.append({"time" : 0,"position" : r,"velocity" : v})
    for i in range(step):
        new_position, new_velocity = euler_step(new_position,new_velocity,dt)
        trajectory.append({
            "time" : (i+1)*dt,
            "position" : new_position,
            "velocity" : new_velocity,
        })
    return trajectory

def main():
    r = [7000, 0, 0]
    v = [0, math.sqrt(satellite_orbit.mu / 7000), 0]
    dt = 1
    step = 600
    trajectory = euler_propagate(r,v,dt,step)
    print("----------------------------------------")
    for point in trajectory:
        print(f"Time: {point["time"]}\nPosition: {point["position"]}\nVelocity: {point["velocity"]}")
        print("----------------------------------------")
    print(f"Minimum distance: {min(distances)}")
    print(f"Maximum distance: {max(distances)}")
    for distance in distances:
        print(f"Radial Error: {round(abs(distance-ideal_orbit),5)}")    
        
if __name__ == "__main__":
    main()