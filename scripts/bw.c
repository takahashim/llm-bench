#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <omp.h>
#define N (1024L*1024L*256L) /* 256M doubles = 2GB per array */
int main(){
  double *a=malloc(N*8),*b=malloc(N*8);
  #pragma omp parallel for
  for(long i=0;i<N;i++){a[i]=1.0;b[i]=2.0;}
  double best=0;
  for(int r=0;r<3;r++){
    double t0=omp_get_wtime();
    #pragma omp parallel for
    for(long i=0;i<N;i++) a[i]=b[i];
    double t=omp_get_wtime()-t0;
    double gb=(2.0*N*8)/1e9/t;
    if(gb>best)best=gb;
  }
  printf("copy best: %.1f GB/s\n",best);
  return 0;
}
