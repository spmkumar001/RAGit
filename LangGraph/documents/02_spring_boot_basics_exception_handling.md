# Spring Boot: Basics and Exception Handling

## 1. What Spring Boot Is and Why It Exists

**Spring** is a large framework for building Java applications, centered on the Inversion of Control (IoC) container and dependency injection. Traditional Spring required a lot of manual XML or Java configuration — wiring beans, configuring a servlet container, setting up data sources, and managing dependency versions by hand.

**Spring Boot** sits on top of Spring and removes most of that boilerplate. Its guiding philosophy is **"convention over configuration"**: it makes sensible default assumptions so you can get a production-ready application running with almost no setup. The three pillars are:

- **Auto-configuration** — Boot inspects the classpath and automatically configures beans it thinks you need. If it sees an H2 driver, it configures an in-memory database; if it sees Spring MVC classes, it sets up a `DispatcherServlet`.
- **Starter dependencies** — curated dependency bundles (`spring-boot-starter-web`, `spring-boot-starter-data-jpa`) that pull in compatible, version-aligned libraries so you avoid dependency conflicts.
- **Embedded server** — an embedded Tomcat (or Jetty/Undertow) is bundled, so the app runs as a self-contained executable JAR (`java -jar app.jar`) with no external server to install.

Together these let a developer focus on business logic rather than infrastructure plumbing.

## 2. Anatomy of a Spring Boot Application

The entry point is a class annotated with `@SpringBootApplication`:

```java
@SpringBootApplication
public class TaskForgeApplication {
    public static void main(String[] args) {
        SpringApplication.run(TaskForgeApplication.class, args);
    }
}
```

`@SpringBootApplication` is a convenience annotation combining three others:

- **`@Configuration`** — marks the class as a source of bean definitions.
- **`@EnableAutoConfiguration`** — turns on Boot's auto-configuration machinery.
- **`@ComponentScan`** — scans the current package and sub-packages for components (`@Component`, `@Service`, `@Repository`, `@Controller`) to register as beans.

`SpringApplication.run(...)` bootstraps everything: it creates the `ApplicationContext`, performs component scanning, applies auto-configuration, and starts the embedded server.

## 3. Inversion of Control and Dependency Injection

**Inversion of Control (IoC)** means the framework, not your code, is responsible for creating and wiring objects. The **Spring IoC container** (the `ApplicationContext`) manages the lifecycle of objects called **beans**.

**Dependency Injection (DI)** is how the container supplies a bean's collaborators. Instead of a class doing `new PaymentService()`, it declares that it *needs* a `PaymentService` and the container provides one. This decouples classes, makes them easier to test (you can inject mocks), and centralizes configuration.

Spring supports three injection styles, and **constructor injection is strongly preferred**:

```java
@Service
public class OrderService {
    private final PaymentService payment;

    // Constructor injection: dependency is final, guaranteed non-null,
    // and the class is easy to unit test.
    public OrderService(PaymentService payment) {
        this.payment = payment;
    }
}
```

Constructor injection makes dependencies explicit and immutable, avoids the `null` risks of field injection, and works without Spring in tests. Field injection (`@Autowired` on a field) is concise but discouraged because it hides dependencies and complicates testing.

## 4. Stereotype Annotations and Bean Definitions

Spring registers beans either by scanning **stereotype annotations** on your classes or via `@Bean` methods in configuration classes:

- **`@Component`** — a generic Spring-managed component.
- **`@Service`** — a `@Component` marking business-logic classes (semantic only).
- **`@Repository`** — marks data-access classes; also enables translation of persistence exceptions into Spring's `DataAccessException` hierarchy.
- **`@Controller` / `@RestController`** — marks web request handlers.

For third-party classes you can't annotate, define beans manually:

```java
@Configuration
public class AppConfig {
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
```

## 5. Bean Scopes and Lifecycle

A **scope** controls how many instances of a bean exist and how long they live:

- **singleton** (default) — one shared instance per container. Must be stateless to be thread-safe.
- **prototype** — a new instance every time it's requested.
- **request**, **session**, **application** — web-specific scopes tied to an HTTP request, session, or servlet context.

Lifecycle hooks let beans react to creation and destruction: `@PostConstruct` runs after dependencies are injected; `@PreDestroy` runs before the bean is removed. These are useful for opening/closing resources.

## 6. Building REST APIs

Spring Boot with `spring-boot-starter-web` makes REST endpoints declarative:

```java
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskService service;
    public TaskController(TaskService service) { this.service = service; }

    @GetMapping("/{id}")
    public TaskDto getTask(@PathVariable Long id) {
        return service.findById(id);
    }

    @PostMapping
    public ResponseEntity<TaskDto> create(@RequestBody @Valid TaskDto dto) {
        TaskDto saved = service.create(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }
}
```

Key annotations: `@RestController` (combines `@Controller` + `@ResponseBody`, so return values are serialized to JSON), `@RequestMapping` / `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` for routing, `@PathVariable` for URL segments, `@RequestParam` for query parameters, and `@RequestBody` to deserialize the JSON request body into an object. `ResponseEntity` gives you full control over status code, headers, and body.

## 7. Configuration with `application.properties` / YAML

External configuration lives in `application.properties` or `application.yml` under `src/main/resources`. This keeps environment-specific values out of code:

```properties
server.port=8081
spring.datasource.url=jdbc:postgresql://localhost:5432/taskforge
spring.jpa.hibernate.ddl-auto=validate
logging.level.org.springframework=INFO
```

**Profiles** (`application-dev.yml`, `application-prod.yml`) let you swap configuration per environment, activated with `spring.profiles.active=prod`. You can bind properties to typed objects with `@ConfigurationProperties` or read single values with `@Value("${server.port}")`.

## 8. Why Exception Handling Matters in REST APIs

Without deliberate handling, an uncaught exception bubbles up and Spring Boot returns its default error response (the "Whitelabel Error Page" or a generic JSON body). That's bad for API clients because it may leak stack traces, uses inconsistent formats, and often returns the wrong HTTP status (a "not found" surfacing as a 500).

Good exception handling means: mapping each error to the correct **HTTP status code**, returning a **consistent, structured error body**, hiding internal details from clients, and logging enough for developers to debug. Spring provides a layered toolkit for this.

## 9. Local Handling with `@ExceptionHandler`

`@ExceptionHandler` methods inside a controller catch exceptions thrown by that controller's handler methods:

```java
@RestController
public class TaskController {

    @ExceptionHandler(TaskNotFoundException.class)
    public ResponseEntity<String> handleNotFound(TaskNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
    }
}
```

This is fine for controller-specific logic, but duplicating it across many controllers is not DRY. For application-wide handling you use a global advice (next section).

## 10. Global Handling with `@ControllerAdvice` / `@RestControllerAdvice`

`@RestControllerAdvice` is a specialized `@ControllerAdvice` (which adds `@ResponseBody`) that centralizes exception handling across **all** controllers. This is the recommended production pattern:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(TaskNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(TaskNotFoundException ex) {
        ApiError error = new ApiError(HttpStatus.NOT_FOUND.value(),
                                      ex.getMessage(), Instant.now());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
        String msg = ex.getBindingResult().getFieldErrors().stream()
            .map(f -> f.getField() + ": " + f.getDefaultMessage())
            .collect(Collectors.joining(", "));
        ApiError error = new ApiError(HttpStatus.BAD_REQUEST.value(), msg, Instant.now());
        return ResponseEntity.badRequest().body(error);
    }

    @ExceptionHandler(Exception.class)   // catch-all fallback
    public ResponseEntity<ApiError> handleGeneric(Exception ex) {
        ApiError error = new ApiError(500, "Internal server error", Instant.now());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
```

Best practice is to define specific handlers first and a broad `Exception.class` fallback last, so specific cases are matched before the catch-all.

## 11. Custom Exceptions and a Structured Error Response

Define domain-specific exceptions that carry meaning:

```java
public class TaskNotFoundException extends RuntimeException {
    public TaskNotFoundException(Long id) {
        super("Task not found with id: " + id);
    }
}
```

Extending `RuntimeException` (unchecked) is the common choice so you don't have to declare `throws` everywhere. Pair exceptions with a consistent error DTO:

```java
public record ApiError(int status, String message, Instant timestamp) {}
```

A predictable JSON shape lets frontend and API consumers handle errors uniformly.

## 12. Bean Validation

`spring-boot-starter-validation` integrates Jakarta Bean Validation. Annotate DTO fields and trigger validation with `@Valid`:

```java
public record TaskDto(
    @NotBlank(message = "title is required") String title,
    @Size(max = 500) String description,
    @NotNull @FutureOrPresent LocalDate dueDate) {}
```

When a `@Valid @RequestBody` fails, Spring throws `MethodArgumentNotValidException`, which your global handler converts into a clean 400 response listing the field errors (as shown in section 10). Common constraints include `@NotNull`, `@NotBlank`, `@Size`, `@Min`, `@Max`, `@Email`, and `@Pattern`.

## 13. `ResponseStatusException` and `@ResponseStatus`

For quick cases you can skip a custom handler:

- Annotate a custom exception with `@ResponseStatus(HttpStatus.NOT_FOUND)` and Spring maps it automatically.
- Or throw `ResponseStatusException` directly in a method: `throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Task not found")`. This is convenient for one-off cases without defining a class.

Choose global `@RestControllerAdvice` for consistency across a real API; use these shortcuts for small apps or edge cases.

## 14. The Request Processing Lifecycle

Understanding how a request flows through Spring MVC clarifies where exception handling fits. When an HTTP request arrives at the embedded server, it reaches the **`DispatcherServlet`** — the front controller that orchestrates everything. The flow is:

1. `DispatcherServlet` receives the request.
2. It consults **handler mappings** to find the controller method matching the URL and HTTP verb.
3. **Argument resolvers** bind path variables, query params, and the request body (via `HttpMessageConverter`s that deserialize JSON) into method parameters; validation runs here.
4. The controller method executes business logic and returns a value.
5. For `@RestController`, an `HttpMessageConverter` (Jackson) serializes the return value to JSON.
6. If any step throws, the `DispatcherServlet` routes the exception to a `HandlerExceptionResolver` — which is exactly where `@ExceptionHandler` and `@RestControllerAdvice` plug in.

This is why a centralized advice can catch exceptions from anywhere in the controller layer: they all funnel back through the dispatcher.

## 15. Starters and Dependency Management in Depth

A **starter** is a Maven/Gradle dependency that transitively pulls in a coordinated set of libraries. `spring-boot-starter-web` brings in Spring MVC, Jackson (JSON), validation, and embedded Tomcat all at once, with versions guaranteed to be compatible. The **Spring Boot parent POM** (or the dependency management BOM) centrally manages versions, so you typically omit version numbers in your own dependencies and let Boot pick tested combinations. This eliminates the notorious "dependency hell" of manually aligning dozens of library versions. Common starters include `spring-boot-starter-data-jpa` (Hibernate + Spring Data), `spring-boot-starter-security`, `spring-boot-starter-test` (JUnit 5, Mockito, AssertJ), and `spring-boot-starter-validation`.

## 16. Spring Data JPA and the Repository Pattern

Most real Spring Boot apps persist data through **Spring Data JPA**, which drastically reduces boilerplate. You define an interface extending `JpaRepository`, and Spring generates the implementation at runtime:

```java
public interface TaskRepository extends JpaRepository<Task, Long> {
    List<Task> findByStatus(String status);       // derived query
    Optional<Task> findByTitle(String title);
}
```

`JpaRepository` provides `save`, `findById`, `findAll`, `delete`, and paging for free. **Derived query methods** are parsed from the method name (`findByStatusAndPriority`) into SQL automatically, and `@Query` lets you write custom JPQL or native SQL when needed. This pairs naturally with exception handling: a lookup returning `Optional.empty()` is where you throw your custom `TaskNotFoundException`, which the global advice then maps to a 404.

## 17. Logging Exceptions Properly

Returning a clean error to the client is only half the job — you must also log enough for developers to diagnose issues. The discipline: log the **full stack trace** server-side (at `ERROR` for unexpected failures, often `WARN` or `INFO` for expected client errors like validation), but return only a **safe, generic message** to the client. Never expose stack traces, SQL, or internal class names in API responses, as they leak implementation details and create security risk.

```java
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> handleGeneric(Exception ex) {
    log.error("Unhandled exception", ex);   // full trace to logs
    return ResponseEntity.status(500)
        .body(new ApiError(500, "Internal server error", Instant.now()));
}
```

A correlation/trace ID attached to each request and echoed in both the log and the error response makes production debugging far easier.

## 18. Testing Controllers and Exception Handlers

Exception handling should be tested, not assumed. `@WebMvcTest` loads only the web layer (fast) and `MockMvc` simulates HTTP requests so you can assert on status codes and response bodies:

```java
@WebMvcTest(TaskController.class)
class TaskControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean TaskService service;

    @Test
    void returns404WhenTaskMissing() throws Exception {
        when(service.findById(99L)).thenThrow(new TaskNotFoundException(99L));
        mockMvc.perform(get("/api/tasks/99"))
               .andExpect(status().isNotFound())
               .andExpect(jsonPath("$.status").value(404));
    }
}
```

This verifies that your `@RestControllerAdvice` actually converts the exception into the intended 404 response. For full integration tests, `@SpringBootTest` starts the whole context.

## 19. Spring Boot Actuator and Observability

`spring-boot-starter-actuator` exposes production-ready endpoints for monitoring and management over HTTP or JMX. `/actuator/health` reports liveness/readiness (used by Kubernetes probes), `/actuator/metrics` exposes performance metrics (integrating with Micrometer and Prometheus), `/actuator/info` shows build info, and others expose environment, loggers, and beans. In production you secure these endpoints and expose only what's needed. Actuator complements good exception handling by giving you visibility into error rates and system health, closing the loop between handling failures gracefully and knowing when they occur.

## 20. Interview Talking Points and Pragmatism

- `@SpringBootApplication` = `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`.
- Prefer **constructor injection**; it makes dependencies explicit, final, and testable.
- Singleton beans are shared — keep them **stateless**.
- Centralize error handling in a single `@RestControllerAdvice` and return a consistent error DTO with the correct HTTP status.
- Map validation failures (`MethodArgumentNotValidException`) to **400 Bad Request**, "not found" to **404**, and unexpected errors to **500** with a generic message (never leak stack traces).
- Keep it pragmatic: a global advice, a handful of meaningful custom exceptions, and Bean Validation cover the vast majority of real needs. Avoid over-engineering with elaborate exception hierarchies when a few well-named exceptions suffice.
