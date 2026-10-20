import math
import vector_operations
mu = 398600.44
earth_radius = 6371
def magnitude(r):
  total = 0
  for axis in r:
    total += axis ** 2
  return math.sqrt(total)
def grav_acc(r):
  A = []
  k = -mu/(magnitude(r)**3)
  A.append(k*r[0])
  A.append(k*r[1])
  A.append(k*r[2])
  return A

def state_vector(r,v):
  return r + v

def vector_towards_ascending_node(h):
  k = [0,0,1]
  return vector_operations.cross_product(k,h)

def angular(r,v):
  return vector_operations.cross_product(r,v)
  
def eccentricity(r,v,h):
  temp = []
  temp = vector_operations.cross_product(v,h)
  temp = vector_operations.scalar(temp,1/mu)
  mag = vector_operations.scalar(r,1/magnitude(r))
  return vector_operations.subtraction(temp,mag)
  
def specific_orbital_energy(r,v):
  return (magnitude(v)**2)/2 - mu/magnitude(r)

def argument_with_perigee(n,e):
  ω = math.degrees(math.acos(vector_operations.dot_product(n,e)/(magnitude(n)*magnitude(e))))
  if e[2] >= 0:
    return ω
  else:
    return 360 - ω

def true_anomaly(r,e,v):
  anomaly = math.degrees(math.acos(vector_operations.dot_product(r,e)/(magnitude(r)*magnitude(e))))
  if vector_operations.dot_product(r,v)>=0:
    return anomaly
  else:
    return 360 - anomaly
  
def semi_major(r,v):
  return -mu/(2*specific_orbital_energy(r,v))

def validate(r,v):
  if magnitude(r) == 0:
    raise ValueError("Position vector can't be 0")
  elif magnitude(v) == 0:
    raise ValueError("Velocity vector can't be 0")
  else:
    return

def satellite_parameter_calc(r,v):
  grav_acc_vector = grav_acc(r)
  a = semi_major(r,v)
  angular_momentum = angular(r,v)
  e = eccentricity(r,v,angular_momentum)
  ecc = magnitude(e)
  rp = a*(1-ecc)
  ra = a*(1+ecc)
  node_vector = vector_towards_ascending_node(angular_momentum)
  inclination = math.degrees(math.acos(angular_momentum[2]/magnitude(angular_momentum)))
  return (grav_acc_vector,a,angular_momentum,e,ecc,rp,ra,node_vector,inclination)

def main():
  r = [5000,4000,3000]
  v = [-2,6,3]
  validate(r,v)
  results = satellite_parameter_calc(r,v)
  grav_acc_vector,a,angular_momentum,e,ecc,rp,ra,node_vector,inclination = results
  print(f"Position vector of satellite: {r}\nVelocity vector of satellite: {v}")
  print(f"State Vector: {state_vector(r,v)}")
  print(f"Distance from Earth: {round(magnitude(r),3)}")
  print(f"Gravitational Acceleration: {[round(grav,5) for grav in grav_acc_vector]}")
  print(f"Specific Orbital Energy: {specific_orbital_energy(r,v):.2f}km^2/s^2")
  print(f"Semi major axis: {a:.2f}km")
  print(f"Angular Momentum: {angular_momentum}km^2/s")
  print(f"The eccentricity vector: {[round(eccen,5) for eccen in e]}")
  print(f"The magnitude of eccentricity; {ecc:.2f}")
  print(f"The perigee radius: {rp:.2f}km\nThe apogee radius: {ra:.2f}km")
  print(f"Orbital period: {2*math.pi*math.sqrt(a**3/mu)/3600:.2f} hours")
  print(f"The inclination angle: {inclination:.2f} degrees")
  if magnitude(node_vector) < 1e-6:
    print("The RAAN of the orbit: Undefined (equatorial orbit)")
  else:
      if node_vector[1] > 0:
          raan = math.acos(node_vector[0]/magnitude(node_vector))
      else:
          raan = 2*math.pi - math.acos(node_vector[0]/magnitude(node_vector))
      print(f"The RAAN of the orbit: {math.degrees(raan):.2f} degrees")
  if ecc != 0 and magnitude(node_vector) != 0:
      print(f"The argument of perigee: {argument_with_perigee(node_vector,e):.2f} degrees")
      print(f"The true anomaly angle of satellite: {true_anomaly(r,e,v):.2f} degrees")
  if earth_radius > rp: 
    print("It intersects the planet.\nNot a valid trajectory.")
  if ecc < 1e-6:
    print("It is a circular orbit")
    print(f"The argument of perigee: Undefined as Circular Orbit")
    print(f"The true anomaly angle of satellite: Undefined as Circular Orbit")
  elif 0 < ecc < 1:
    print("It is an elliptical orbit")
  elif ecc == 1:
    print("It is a parabolic trajectory")
  else:
    print("It is a hyperbolic trajectory")
    
if __name__=="__main__":
  main()
