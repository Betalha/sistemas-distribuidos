FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /b
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src src
RUN mvn -q -B package -DskipTests
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /b/target/lib/ lib/
COPY --from=build /b/target/music-1.jar lib/
ENTRYPOINT ["java", "-cp", "lib/*", "music.Main"]
