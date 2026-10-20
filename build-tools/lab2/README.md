# Lab 2 — Maven Build Tool

A Java calculator built with Maven to practice its build lifecycle: compile, test, package into a JAR, and run it.

**Repository:** https://github.com/Ibrahim-Adel15/CalculatorMavenApp

## Project Structure

```
lab2/
├── pom.xml
└── src/
    ├── main/java/com/example/calculator/
    │   ├── Calculator.java   # sum, subtract, multiply, divide
    │   └── Main.java         # CLI entry point
    └── test/java/com/example/calculator/
        └── CalculatorTest.java  # JUnit 5 tests
```

## Steps

### 1. Install prerequisites

Java 17 was already installed. Maven was installed with:

```bash
sudo apt install maven
```

The `pom.xml` sets `maven.compiler.source` and `maven.compiler.target` to `17`.

### 2. Clone the repository

```bash
git clone https://github.com/Ibrahim-Adel15/CalculatorMavenApp
```

### 3. Run the tests

```bash
mvn test
```

Maven compiles the main and test sources, then runs the tests with the Surefire plugin.

```
[INFO] Running com.example.calculator.CalculatorTest
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.074 s
[INFO]
[INFO] Results:
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### 4. Package the application

```bash
mvn package
```

Runs the full lifecycle through `test` and then builds the JAR with the `maven-jar-plugin`, producing `target/calculator.jar` with `Main-Class` set so it is executable.

```
[INFO] --- jar:3.4.1:jar (default-jar) @ calculator ---
[INFO] BUILD SUCCESS
[INFO] Total time:  3.186 s
```

### 5. Run the application

```bash
java -jar target/calculator.jar
```

```
Enter first number: 30
Enter second number: 25
a = 30.0, b = 25.0
Sum: 55.0
Subtract: 5.0
Multiply: 750.0
Divide: 1.2
```

## Key Commands

| Command | Purpose |
| --- | --- |
| `mvn compile` | Compile main sources |
| `mvn test` | Compile and run tests |
| `mvn package` | Compile, test, and build `target/calculator.jar` |
| `mvn clean` | Delete the `target/` directory |
| `java -jar target/calculator.jar` | Run the application |

## Notes

- Tests: `sum`, `subtract`, `multiply`, `divide`, and `divide` by zero throwing `ArithmeticException` (5 tests, all passing).
- `finalName` is set to `calculator`, which is why the artifact is `target/calculator.jar` rather than `calculator-1.0.0.jar`.
