int x = 5;
float y = 5.7;

extern int __ikos_unknown();

void incr_x() {
  if (__ikos_unknown())
    x++;
}

void incr_y() {
  if (__ikos_unknown())
    y = y + 1.0;
}

int main() {
  int a;

  incr_x();
  a = x;

  float b;
  incr_y();
  b = y;

  int c = a + (int)b;
  return c;
}
