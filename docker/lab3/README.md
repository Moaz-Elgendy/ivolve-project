# Lab 3 — Dockerizing a Java Application

The same Maven calculator app is containerized in two ways to compare image size:

- **Part 1** — build inside the image using a Maven base image.
- **Part 2** — build the JAR first, then copy only the artifact into a JRE image.

## Project Files

```
lab3/
├── Dockerfile.maven      # Part 1
├── Dockerfile.java-image # Part 2
├── pom.xml
└── target/calculator.jar # built with mvn package
```

---

## Part 1 — Build inside the image

### Dockerfile.maven

```dockerfile
FROM maven:3.10.0-eclipse-temurin-17

WORKDIR /app

COPY --chown=ubuntu:ubuntu . .

RUN chown -R ubuntu:ubuntu /app

USER ubuntu

RUN mvn package

CMD ["java", "-jar", "target/calculator.jar"]

EXPOSE 8080
```

### Why `USER ubuntu` comes after `WORKDIR`, `COPY`, and `RUN chown`

Docker runs instructions as `root` until a `USER` instruction changes it, and that change applies to **all following** instructions.

If `USER ubuntu` were placed before `WORKDIR` / `COPY` / `RUN`, the build would break:

- `WORKDIR /app` would try to create `/app` at the filesystem root as `ubuntu`, which is not allowed.
- `COPY . .` creates files owned by `root` by default, so `ubuntu` could not write into `/app`.
- `RUN mvn package` runs as `ubuntu` and needs to write `target/` inside `/app` and download dependencies into `~/.m2`. Both writes fail with `Permission denied` on root-owned paths.

Placing the user switch later avoids this: the directory and files are created while still `root`, ownership is handed to `ubuntu` with `COPY --chown=ubuntu:ubuntu` and `RUN chown -R ubuntu:ubuntu /app`, and only then does the build run as `ubuntu`. The result is that `mvn package` and the final `CMD` both run as a non-root user, with no permission conflicts.

### Build and run

```bash
docker build -t app1:v1 . -f Dockerfile.maven
docker run --name container1 -it app1:v1
```

```
Enter first number: 20
Enter second number: 30
a = 20.0, b = 30.0
Sum: 50.0
Subtract: -10.0
Multiply: 600.0
Divide: 0.6666666666666666
```

The app reads input, prints results, and exits normally once finished:

```
CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS                     PORTS   NAMES
f2fc045305f9   app1:v1   "/usr/local/bin/mvn-…"   About a minute ago   Exited (0) About a minute ago           container1
```

### Image size

```
REPOSITORY   TAG   IMAGE ID       CREATED   SIZE
app1         v1    026648b1107c   ...       861MB
```

---

## Part 2 — Build first, ship only the JAR

### Build the artifact

```bash
mvn package
```

Produces `target/calculator.jar`.

### Dockerfile.java-image

```dockerfile
FROM eclipse-temurin:17-jre

WORKDIR /app

COPY --chown=ubuntu:ubuntu target/calculator.jar .

USER ubuntu

CMD ["java", "-jar", "calculator.jar"]

EXPOSE 8080
```

This image contains only a JRE and the built artifact — no Maven, no source code, no test dependencies.

### Build and run

```bash
docker build -t app2:v1 . -f Dockerfile.java-image
docker run --name container2 -it app2:v1
```

```
Enter first number: 90
Enter second number: 25
a = 90.0, b = 25.0
Sum: 115.0
Subtract: 65.0
Multiply: 2250.0
Divide: 3.6
```

### Image size

```
REPOSITORY   TAG   IMAGE ID       CREATED   SIZE
app2         v1    77ffe1361af3   ...       427MB
```

---

## Comparison

| | Part 1 — `app1:v1` | Part 2 — `app2:v1` |
| --- | --- | --- |
| Base image | `maven:3.10.0-eclipse-temurin-17` | `eclipse-temurin:17-jre` |
| Build happens | Inside the image (`RUN mvn package`) | Before the build (`mvn package` on host) |
| Copied into image | Full source code | Only `target/calculator.jar` |
| Maven + JDK present at runtime | Yes | No |
| Image size | **861 MB** | **427 MB** |

Part 2 is about **half the size** (434 MB smaller).

The reason is that Part 1 keeps everything needed to *build* the application inside the final image: the full Maven distribution, the JDK, the source tree, and all the layers created while compiling it. None of that is needed to *run* the app — only the JAR and a JRE are. Shipping Maven and the whole source is unnecessary weight that is never used at runtime, and copying the entire application into the image makes less sense than copying the single artifact it produces.

## Notes

- `EXPOSE 8080` is documentation only here; this is a CLI application with no network listener.
- Part 1 could be improved into a multi-stage build so Maven stays in the build stage and only the JAR is copied into the final JRE image — the same result achieved manually in Part 2.
