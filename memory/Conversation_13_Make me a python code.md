# Make me a python code
**Exported:** 2026-04-05 21:54:33

---

### USER (2026-04-05 16:24:33)
Make me a python code to display a circle

### JARVIS (2026-04-05 21:54:40)
Here is a Python code snippet to display a circle using `matplotlib`:


```python
import matplotlib.pyplot as plt
import numpy as np

theta = np.linspace(0, 2*np.pi, 100)
r = 1 # radius of the circle
x = r * np.cos(theta)
y = r * np.sin(theta)

fig, ax = plt.subplots(1)
ax.plot(x, y)
ax.set_aspect('equal', adjustable='box')
plt.title("Circle")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.grid(True)
plt.show()
```

