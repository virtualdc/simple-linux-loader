int x = 100500;

void foo()
{
    x += 5;
}

void bar()
{
    x += 3;
}

int main()
{
    foo();
    bar();
    foo();
    bar();
    return x;
}
