fn fibonacci(n: i32) -> () {
    if (n <= 1) {
        return n;
    } else {
        return (        fibonacci((n - 1)) +         fibonacci((n - 2)));
    }
}
fn main() {
println!("Fibonacci sequence:");
for i in 0..10 {
    println!("{}",     fibonacci(i));
}
}