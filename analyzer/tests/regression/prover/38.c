extern void __ikos_assert(int);
extern int __ikos_unknown();

int main(int argc, char** argv) {
  int n = __ikos_unknown();
  int x = 0;
  int y = 0;
  int i = 0;

  if (n < 0)
    return 0;
  while (i < n) {
    i++;
    x++;
    if (i % 2 == 0)
      y++;
  }

  if (i % 2 == 0) {
    __ikos_assert(x == 2 * y);
  }
}
