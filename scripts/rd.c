#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <immintrin.h>
/* 重み読み出しと同じパターン: 巨大配列の純ストリーミングread */
#define N (1024L*1024L*512L)  /* 512M floats = 2GB */
int main(int argc,char**argv){
  int nt = atoi(argv[1]);
  float *a = aligned_alloc(64, N*4);
  #pragma omp parallel for num_threads(nt)
  for(long i=0;i<N;i++) a[i]=1.0f;
  double best=0;
  for(int r=0;r<4;r++){
    double t0=omp_get_wtime();
    double s=0;
    #pragma omp parallel num_threads(nt) reduction(+:s)
    {
      __m256 acc=_mm256_setzero_ps();
      #pragma omp for
      for(long i=0;i<N;i+=8) acc=_mm256_add_ps(acc,_mm256_load_ps(a+i));
      float t[8]; _mm256_storeu_ps(t,acc);
      for(int k=0;k<8;k++) s+=t[k];
    }
    double dt=omp_get_wtime()-t0;
    double gb=(double)N*4/1e9/dt;
    if(gb>best)best=gb;
    if(s<0)printf("x");
  }
  printf("threads=%2d  pure read: %.1f GB/s  (%.0f%% of 89.6 peak)\n",nt,best,best/89.6*100);
  return 0;
}
