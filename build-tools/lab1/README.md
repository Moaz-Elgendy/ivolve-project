# Lab 1 — Gradle Build Tool

A simple Java calculator built with Gradle to practice the build lifecycle: compile, test, build a JAR, and run it.

## Project Structure

```
lab1/
├── build.gradle
├── settings.gradle
├── gradlew / gradlew.bat
├── gradle/wrapper/
└── src/
    ├── main/java/com/example/calculator/
    │   ├── Calculator.java   # sum, subtract, multiply, divide
    │   └── Main.java         # CLI entry point
    └── test/java/com/example/calculator/
        └── CalculatorTest.java  # JUnit 5 tests
```

## Steps

### 1. Install the JDK

```bash
sudo apt install openjdk-17-jdk -y
```

`build.gradle` uses a Java 17 toolchain, so this is the required JDK version.

### 2. Generate the Gradle Wrapper

Gradle was already installed locally, so I used it to generate the wrapper, pinning the project to Gradle 9.3.1:

```bash
~/.gradle/wrapper/dists/gradle-9.3.1-all/9ot9r568e8zfvvd4mn8rbu1j0/gradle-9.3.1/bin/gradle wrapper --gradle-version 9.3.1
```

This creates `gradlew`, `gradlew.bat`, and `gradle/wrapper/`, so anyone can build the project without installing Gradle.

### 3. Compile and run the tests

```bash
./gradlew test
```

This compiles the main sources, compiles the test sources, then runs the JUnit tests.

```
BUILD SUCCESSFUL in 1s
3 actionable tasks: 3 up-to-date
```

### 4. Build the artifact

```bash
./gradlew build
```

This runs compile, test, and packaging, producing `build/libs/calculator.jar` (executable, with `Main-Class` set in the manifest).

```
BUILD SUCCESSFUL in 1s
7 actionable tasks: 4 executed, 3 up-to-date
```

### 5. Run the application

```bash
java -jar build/libs/calculator.jar
```

```
Enter first number: 10
Enter second number: 20
a = 10.0, b = 20.0
Sum: 30.0
Subtract: -10.0
Multiply: 200.0
Divide: 0.5
```

## Key Commands

| Command | Purpose |
| --- | --- |
| `./gradlew test` | Compile and run tests |
| `./gradlew build` | Compile, test, and build the JAR |
| `./gradlew clean` | Delete the `build/` directory |
| `java -jar build/libs/calculator.jar` | Run the application |

## Notes

- Tests: `sum`, `subtract`, `multiply`, `divide`, plus `divide` by zero throwing `ArithmeticException`.
- Dividing by zero is guarded in `Calculator.divide`.
- The `application` plugin also allows running from source with `./gradlew run`.
