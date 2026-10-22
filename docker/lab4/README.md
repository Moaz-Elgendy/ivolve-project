# Lab 4 — Docker Multi-Stage Build

A Spring Boot application is containerized twice: first with a single-stage build, then with a multi-stage build. The results are compared by image size, and the final image is saved, removed, and restored.

## Project Files

```
docker/lab4/
├── Dockerfile              # single-stage build
├── Dockerfile.multi-stage  # multi-stage build
├── pom.xml                 # Spring Boot 3.2.0, Java 17
├── src/
└── lab-image.tar           # exported image2
```

---

## Part 1 — Single-stage build

### Dockerfile

```dockerfile
FROM maven:3.9.15-eclipse-temurin-17-alpine

WORKDIR /app

COPY . .

RUN mvn package

EXPOSE 8080

CMD ["java", "-jar", "target/demo-0.0.1-SNAPSHOT.jar"]
```

Everything is built and run in the same image, so Maven, the JDK, and the full source tree stay inside the final image.

### Build, size, and run

```bash
docker build -t image1:latest .
docker images | grep -i "image1"
```

```
image1   latest   a4e5a6708e30   671MB
```

```bash
docker run --name container1 image1:latest
```

The container started and the application ran successfully.

---

## Part 2 — Multi-stage build

### Dockerfile.multi-stage

```dockerfile
FROM maven:3.9.15-eclipse-temurin-17-alpine AS builder

WORKDIR /app

COPY pom.xml .

COPY src ./src

RUN mvn package

FROM eclipse-temurin:17-jre

WORKDIR /app

RUN addgroup --system java && adduser --system --ingroup java java

COPY --chown=java:java --from=builder /app/target/demo-0.0.1-SNAPSHOT.jar .

USER java

EXPOSE 8080

CMD ["java", "-jar", "demo-0.0.1-SNAPSHOT.jar"]
```

- **Stage 1 (`builder`)** has Maven and the source, resolves dependencies, and produces the JAR.
- **Stage 2** starts from a plain JRE and copies only the JAR from the builder, so Maven and the source never reach the final image.
- A dedicated non-root `java` user is created and given ownership of the JAR, and `USER java` makes the container run as that user.

### Build and run

```bash
docker build -t image2 -f Dockerfile.multi-stage .
docker run -itd --name container2 image2
d49ce52236572177340ae82561585df1197704c1423e03aabbd8820770dfa81a
```

### Verify the non-root user

```bash
docker exec container2 whoami
java
```

The process runs as `java`, not `root`.

### Clean up the container

```bash
docker stop container2
docker rm container2
```

---

## Part 3 — Save, remove, and restore the image

```bash
docker save -o lab-image.tar image2
ls -lah lab-image.tar
```

```
-rw------- 1 moaz moaz 122M Oct 22 01:00 lab-image.tar
```

The image was then deleted and restored from the archive:

```bash
docker rmi image2
docker load -i lab-image.tar
docker images | grep -i "image2"
```

```
image2   latest   6600e8ca4994   464MB
```

The restored image is available again and keeps the same size.

---

## Comparison

| | Part 1 — `image1:latest` | Part 2 — `image2` |
| --- | --- | --- |
| Build type | Single-stage | Multi-stage |
| Base image (final) | `maven:...-alpine` | `eclipse-temurin:17-jre` |
| Maven / JDK in final image | Yes | No (build stage only) |
| Source code in final image | Yes | No, only the JAR |
| Runs as non-root | No | Yes (`java`) |
| Image size | **671 MB** | **464 MB** |

The multi-stage build is **207 MB smaller** because the compiler, Maven, the downloaded dependencies, and the source files are discarded with the builder stage. Only the JRE and the runnable JAR remain.

## Notes

- `EXPOSE 8080` documents the Spring Boot port; no `-p` mapping is required to run the container.
- `docker save` writes the image layers into one archive file, so `lab-image.tar` (122 MB) is not directly comparable to the `docker images` size, which includes shared base-image layers.
