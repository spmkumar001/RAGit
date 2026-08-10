# Core Java: Multithreading and Concurrency

## 1. Processes vs Threads

A **process** is an independent program in execution with its own memory space (heap, stack, code, data). Processes are isolated from each other; inter-process communication is relatively expensive and goes through the operating system.

A **thread** is the smallest unit of execution *within* a process. Multiple threads inside one process share the same heap memory and class metadata, but each thread has its **own stack**, program counter, and local variables. Because threads share heap memory, communication between them is cheap — but this sharing is also the source of most concurrency bugs.

In Java, every application starts with at least one thread: the **main thread**, created by the JVM. Additional threads (like the garbage collector) run in the background. Multithreading lets a program do several things at once — for example, handle many HTTP requests concurrently, or keep a UI responsive while doing background work.

**Concurrency vs parallelism** is a distinction interviewers love. *Concurrency* is about dealing with many tasks at once (structure) — tasks may be interleaved on a single core. *Parallelism* is about executing many tasks literally simultaneously on multiple cores. Concurrency is a design property; parallelism is an execution property.

## 2. The Thread Lifecycle

A Java thread moves through well-defined states, represented by the `Thread.State` enum:

- **NEW** — the `Thread` object is created but `start()` has not been called.
- **RUNNABLE** — the thread is eligible to run; it may be actually running or waiting for CPU time. Java does not distinguish "ready" from "running" at the API level.
- **BLOCKED** — the thread is waiting to acquire a monitor lock (to enter a `synchronized` block already held by another thread).
- **WAITING** — the thread is waiting indefinitely for another thread to signal it (e.g., `Object.wait()`, `Thread.join()` with no timeout, `LockSupport.park()`).
- **TIMED_WAITING** — like WAITING but with a timeout (`sleep(ms)`, `wait(ms)`, `join(ms)`).
- **TERMINATED** — the `run()` method has completed or thrown an uncaught exception.

Calling `start()` twice on the same thread throws `IllegalThreadStateException`. A key beginner mistake is calling `run()` directly instead of `start()`: `run()` just executes the code on the current thread synchronously, while `start()` asks the JVM to create a new OS thread and invoke `run()` on it.

## 3. Creating Threads: Four Approaches

**Extending Thread.** Subclass `Thread` and override `run()`. This is discouraged because Java has single inheritance — extending `Thread` uses up your one inheritance slot and tightly couples the task to the thread.

```java
class MyThread extends Thread {
    public void run() { System.out.println("Running"); }
}
new MyThread().start();
```

**Implementing Runnable.** `Runnable` is a functional interface with a single `run()` method that returns nothing and cannot throw checked exceptions. This is preferred because it separates the *task* (what to do) from the *worker* (the thread). Since Java 8 it can be a lambda.

```java
Runnable task = () -> System.out.println("Running");
new Thread(task).start();
```

**Implementing Callable + Future.** `Callable<V>` returns a value and may throw checked exceptions. It is submitted to an `ExecutorService`, which returns a `Future<V>`. Calling `future.get()` blocks until the result is ready.

```java
Callable<Integer> c = () -> 42;
Future<Integer> f = executor.submit(c);
Integer result = f.get(); // blocks
```

**ExecutorService / thread pools.** In production you almost never create raw threads. Instead you submit tasks to a managed pool (see section 8). This is the modern, recommended approach.

## 4. Synchronization and the `synchronized` Keyword

When multiple threads read and write shared mutable state without coordination, you get a **race condition** — the result depends on unpredictable thread scheduling. The classic example is `count++`, which is actually three operations (read, increment, write) and is therefore **not atomic**.

The `synchronized` keyword provides **mutual exclusion**: only one thread can hold a given object's *monitor lock* at a time.

```java
public synchronized void increment() { count++; }      // locks 'this'
public static synchronized void m() { ... }             // locks the Class object
synchronized (lockObject) { /* critical section */ }    // locks a specific object
```

`synchronized` guarantees two things: **atomicity** of the critical section relative to other synchronized blocks on the same lock, and **visibility** — changes made by one thread inside the block become visible to the next thread that acquires the same lock (a happens-before relationship). Locking on different objects gives no protection; both threads must synchronize on the *same* monitor.

## 5. `volatile`, Atomics, and Visibility

**The visibility problem:** without synchronization, one thread's writes to a field may sit in a CPU cache or register and never become visible to another thread, which could loop forever reading a stale value.

**`volatile`** guarantees visibility and ordering but *not* atomicity. A read of a volatile field always sees the most recent write, and the compiler/CPU cannot reorder operations across it. Use `volatile` for a simple flag (like `private volatile boolean running`) that one thread writes and others read. It does **not** make `count++` safe, because that is a compound operation.

**Atomic classes** (`AtomicInteger`, `AtomicLong`, `AtomicReference`, etc.) provide lock-free, thread-safe compound operations using CPU compare-and-swap (CAS) instructions. `atomicInt.incrementAndGet()` is atomic and usually faster than a `synchronized` block under contention.

```java
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();          // atomic ++
counter.compareAndSet(5, 10);       // CAS
```

## 6. `wait()`, `notify()`, and Inter-Thread Coordination

`wait()`, `notify()`, and `notifyAll()` are methods on `Object` and can only be called while holding that object's monitor (inside a `synchronized` block on it) — otherwise you get `IllegalMonitorStateException`.

- `wait()` releases the lock and suspends the thread until notified.
- `notify()` wakes one waiting thread; `notifyAll()` wakes all of them.

The canonical pattern uses `wait()` inside a **while loop** (never an `if`) to guard against **spurious wakeups** and to re-check the condition:

```java
synchronized (queue) {
    while (queue.isEmpty()) {
        queue.wait();
    }
    process(queue.poll());
}
```

This is the basis of the producer–consumer pattern. In modern code, higher-level tools like `BlockingQueue`, `Condition`, `CountDownLatch`, and `Semaphore` usually replace raw `wait/notify`.

## 7. Deadlock, Livelock, and Starvation

**Deadlock** occurs when two or more threads each hold a lock the other needs, so none can proceed. It requires four conditions (Coffman conditions): mutual exclusion, hold-and-wait, no preemption, and circular wait. The most common real-world cause is acquiring multiple locks in inconsistent order. The standard fix is **lock ordering** — always acquire locks in the same global order — or using `tryLock()` with a timeout.

**Livelock** is when threads keep responding to each other and changing state but make no progress (like two people stepping aside repeatedly in a hallway). **Starvation** happens when a thread never gets CPU time or a lock because greedy or higher-priority threads monopolize the resource. Fair locks (`new ReentrantLock(true)`) help mitigate starvation.

## 8. The Executor Framework and Thread Pools

Creating a new thread per task is expensive (memory + OS overhead) and unbounded thread creation can crash the JVM. The **Executor framework** (`java.util.concurrent`) manages a pool of reusable worker threads.

- `Executors.newFixedThreadPool(n)` — fixed number of threads.
- `Executors.newCachedThreadPool()` — grows and shrinks on demand; good for many short tasks.
- `Executors.newSingleThreadExecutor()` — one worker, tasks run sequentially.
- `Executors.newScheduledThreadPool(n)` — for delayed and periodic tasks.
- `Executors.newVirtualThreadPerTaskExecutor()` — Java 21+ virtual threads.

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
pool.submit(() -> doWork());
pool.shutdown();                    // no new tasks; finishes queued ones
pool.awaitTermination(30, TimeUnit.SECONDS);
```

For fine control, construct a `ThreadPoolExecutor` directly with core size, max size, keep-alive time, work queue, and a rejection policy. Interviewers often ask what happens when the queue is full: the configured `RejectedExecutionHandler` (e.g., `AbortPolicy`, `CallerRunsPolicy`) decides.

## 9. Locks: `ReentrantLock` and `ReadWriteLock`

The `java.util.concurrent.locks` package offers more flexibility than `synchronized`:

- **`ReentrantLock`** supports `tryLock()`, timed lock attempts, interruptible locking, and optional fairness. You must `unlock()` in a `finally` block.
- **`ReadWriteLock`** allows multiple concurrent readers but exclusive writers — ideal for read-heavy data.
- **`StampedLock`** (Java 8) adds optimistic reads for even better read performance.

```java
Lock lock = new ReentrantLock();
lock.lock();
try { /* critical section */ }
finally { lock.unlock(); }
```

Prefer `synchronized` for simple cases (it's cleaner and the JVM optimizes it well); reach for explicit `Lock`s when you need tryLock, timeouts, fairness, or multiple condition variables.

## 10. Concurrent Collections

Wrapping collections with `Collections.synchronizedList()` locks the whole structure per operation and doesn't make compound operations safe. The `java.util.concurrent` collections are purpose-built:

- **`ConcurrentHashMap`** — high-throughput map using fine-grained locking / CAS; reads are mostly lock-free. Provides atomic methods like `computeIfAbsent`, `putIfAbsent`, `merge`.
- **`CopyOnWriteArrayList`** — copies the backing array on each write; excellent for read-heavy, write-rare scenarios (e.g., listener lists).
- **`BlockingQueue`** implementations (`ArrayBlockingQueue`, `LinkedBlockingQueue`) — the backbone of producer–consumer designs; `put()` blocks when full, `take()` blocks when empty.
- **`ConcurrentLinkedQueue`** — lock-free unbounded queue.

## 11. CompletableFuture and Asynchronous Composition

`CompletableFuture<T>` (Java 8) models an asynchronous computation you can chain and combine without blocking:

```java
CompletableFuture.supplyAsync(() -> fetchUser(id))
    .thenApply(user -> user.getEmail())
    .thenAccept(email -> send(email))
    .exceptionally(ex -> { log(ex); return null; });
```

Key methods: `thenApply` (transform), `thenCompose` (chain another future — flatMap), `thenCombine` (merge two futures), `allOf`/`anyOf` (wait for many), and `exceptionally`/`handle` (error handling). This enables non-blocking pipelines that are far more composable than raw `Future.get()`.

## 12. The Java Memory Model (JMM) and happens-before

The **JMM** defines when a write by one thread is guaranteed visible to a read by another. The core concept is the **happens-before** relationship: if action A happens-before action B, then A's effects are visible to B. Key happens-before rules include: a `synchronized` unlock happens-before a later lock on the same monitor; a write to a `volatile` field happens-before every later read of it; `Thread.start()` happens-before any action in the started thread; and every action in a thread happens-before another thread's successful `join()` on it. Without a happens-before edge, the JVM is free to reorder and cache, and you cannot assume any particular ordering.

## 13. Virtual Threads (Project Loom, Java 21+)

**Virtual threads** are lightweight threads managed by the JVM rather than the OS. You can create millions of them cheaply. A virtual thread that blocks (on I/O) is "unmounted" from its carrier OS thread, freeing that carrier for other work. This lets you write simple blocking-style code that scales like asynchronous code, largely removing the need for reactive frameworks in many server workloads. `Thread.ofVirtual().start(task)` or `Executors.newVirtualThreadPerTaskExecutor()` create them.

## 14. ThreadLocal: Per-Thread State

`ThreadLocal<T>` gives each thread its own independent copy of a variable, avoiding sharing entirely. Instead of synchronizing access to shared state, each thread reads and writes its own value:

```java
private static final ThreadLocal<SimpleDateFormat> formatter =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

String today = formatter.get().format(new Date());
```

This is the standard fix for non-thread-safe objects like `SimpleDateFormat` and is widely used to carry per-request context (user ID, transaction ID) through a call stack without passing parameters everywhere. A crucial caveat: in thread-pool environments, threads are reused, so a stale `ThreadLocal` value can leak into the next task. Always call `remove()` when done (often in a `finally` block or a servlet filter) to prevent memory leaks and data bleed between requests.

## 15. The Fork/Join Framework and Parallel Streams

The **Fork/Join framework** (`ForkJoinPool`, Java 7) is designed for **divide-and-conquer** parallelism: a large task recursively splits ("forks") into subtasks until they're small enough to compute directly, then results are combined ("joined"). Its key innovation is **work-stealing** — idle worker threads steal queued subtasks from busy threads, keeping all cores utilized.

```java
class SumTask extends RecursiveTask<Long> {
    protected Long compute() {
        if (small enough) return computeDirectly();
        SumTask left = ...;  SumTask right = ...;
        left.fork();                       // async
        return right.compute() + left.join();
    }
}
```

The common `ForkJoinPool` also powers **parallel streams**: `list.parallelStream().filter(...).reduce(...)` automatically splits work across cores. Parallel streams are convenient but only pay off for large datasets and CPU-bound, side-effect-free operations; for small or I/O-bound work they can be slower than sequential due to overhead.

## 16. Coordination Utilities: Latches, Barriers, Semaphores

The `java.util.concurrent` package provides high-level coordinators that are safer and clearer than raw `wait/notify`:

- **`CountDownLatch`** — a one-time gate: threads wait until a counter reaches zero. Useful for "wait until N services have started" or "wait for N tasks to finish."
- **`CyclicBarrier`** — a reusable meeting point where a fixed number of threads wait for each other before all proceed together; ideal for phased parallel computation.
- **`Semaphore`** — maintains a set of permits to limit concurrent access to a resource (e.g., allow only 10 threads to hit a database at once).
- **`Phaser`** — a flexible, reusable barrier supporting a dynamic number of parties.
- **`Exchanger`** — lets two threads swap objects at a synchronization point.

```java
CountDownLatch latch = new CountDownLatch(3);
// worker threads call latch.countDown() when done
latch.await();   // main thread blocks until count hits 0
```

## 17. A Worked Example: Producer–Consumer with BlockingQueue

The producer–consumer pattern is a concurrency classic, and `BlockingQueue` implements it cleanly without manual locking. Producers put items into a bounded queue; consumers take them out; the queue handles all blocking:

```java
BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(10);

Runnable producer = () -> {
    try {
        for (int i = 0; i < 100; i++) queue.put(i); // blocks if full
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
};

Runnable consumer = () -> {
    try {
        while (true) {
            Integer item = queue.take();             // blocks if empty
            process(item);
        }
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
};
```

The queue's internal locking coordinates everything, decoupling production rate from consumption rate — a buffer that smooths bursts. This is the recommended modern replacement for hand-written `wait/notify` producer–consumer code, and it illustrates the general principle: prefer higher-level `java.util.concurrent` abstractions over low-level primitives.

## 18. Handling Interruption Correctly

**Interruption** is Java's cooperative mechanism for asking a thread to stop. Calling `thread.interrupt()` sets the thread's interrupt flag; blocking methods like `sleep()`, `wait()`, and `join()` throw `InterruptedException` in response. A thread is never forcibly killed — it must check for interruption and choose to stop.

Two rules define correct handling: never swallow `InterruptedException` silently, and if you catch it without rethrowing, **restore the interrupt flag** with `Thread.currentThread().interrupt()` so callers up the stack can also observe it. In loops doing long work, periodically check `Thread.currentThread().isInterrupted()` and exit gracefully. The deprecated `Thread.stop()` must never be used — it can leave shared state corrupted.

## 19. Common Interview Talking Points

- `sleep()` holds the lock; `wait()` releases it. `sleep()` is a static `Thread` method, `wait()` is an `Object` method.
- Prefer `Runnable`/`Callable` over extending `Thread`; prefer thread pools over raw threads.
- `count++` is not atomic; use `AtomicInteger` or synchronization.
- Always `wait()` in a loop, not an `if`.
- `ConcurrentHashMap` over `Hashtable`/`synchronizedMap` for concurrent maps.
- Deadlock is prevented by consistent lock ordering.
- `volatile` gives visibility, not atomicity.
- Thread-safety strategies: immutability (best), confinement, synchronization, and lock-free/atomic operations.
