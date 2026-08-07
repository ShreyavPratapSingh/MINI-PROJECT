#include<iostream>
#include<string>
using namespace std;
int main(int argc, char* argv[]){
    if(argc < 2) return 0;
    string data = argv[1]; string encrypted="";
    for(char c: data) encrypted += char(c+3);
    cout<<encrypted;
    return 0;
}