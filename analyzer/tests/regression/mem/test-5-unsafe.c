// DEFINITE UNSAFE
#include <stdint.h>

extern void __ikos_assert(int);
extern int __ikos_unknown();

struct bar {
  int y;
  unsigned char z;
};

struct foo {
  unsigned char a;
  long b;
  unsigned char c;
  struct bar d;
};

int main() {
  struct foo x;
  x.a = 5;
  x.b = 2000;
  x.c = 10;
  x.d.y = 32;
  x.d.z = 5;

  if (x.d.y > 0) {
    __ikos_assert(x.d.y + x.c == 43);
  }
  return 42;
}
