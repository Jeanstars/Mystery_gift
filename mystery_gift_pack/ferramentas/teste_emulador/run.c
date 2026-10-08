#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static FILE* resf; static struct mCore* core; static color_t* buf; static unsigned W,H;
static void shot(const char* fn){ FILE* f=fopen(fn,"wb"); fprintf(f,"P6\n%u %u\n255\n",W,H);
 for(unsigned i=0;i<W*H;i++){ uint32_t c=buf[i]; fputc(c&0xFF,f); fputc((c>>8)&0xFF,f); fputc((c>>16)&0xFF,f);} fclose(f);}
static int keymask(const char* s){ int m=0; if(strstr(s,"A"))m|=1; if(strstr(s,"B"))m|=2; if(strstr(s,"SELECT"))m|=4; if(strstr(s,"START"))m|=8;
 if(strstr(s,"RIGHT"))m|=16; if(strstr(s,"LEFT"))m|=32; if(strstr(s,"UP"))m|=64; if(strstr(s,"DOWN"))m|=128; if(strstr(s,"NONE"))m=0; return m; }
int main(int argc,char**argv){
 resf=fopen("res.txt","w"); core=mCoreFind(argv[1]); core->init(core); mCoreInitConfig(core,NULL);
 core->desiredVideoDimensions(core,&W,&H); buf=malloc(W*H*4); core->setVideoBuffer(core,buf,W);
 mCoreLoadFile(core,argv[1]); core->reset(core);
 FILE* sc=fopen(argv[2],"r"); char line[256];
 while(fgets(line,sizeof line,sc)){
  char cmd[32],a1[128]; unsigned long v=0; a1[0]=0; int n=sscanf(line,"%31s %127s %lx",cmd,a1,&v); if(n<1)continue;
  if(!strcmp(cmd,"run")){ int k=atoi(a1); for(int i=0;i<k;i++) core->runFrame(core); }
  else if(!strcmp(cmd,"press")){ int k=(int)v; sscanf(line,"%*s %127s %d",a1,&k); core->setKeys(core,keymask(a1)); for(int i=0;i<k;i++) core->runFrame(core); core->setKeys(core,0); for(int i=0;i<3;i++) core->runFrame(core);} 
  else if(!strcmp(cmd,"shot")) shot(a1);
  else if(!strcmp(cmd,"w32")) core->busWrite32(core,strtoul(a1,0,16),v);
  else if(!strcmp(cmd,"w16")) core->busWrite16(core,strtoul(a1,0,16),v);
  else if(!strcmp(cmd,"w8")) core->busWrite8(core,strtoul(a1,0,16),v);
  else if(!strcmp(cmd,"r16")) fprintf(resf,"%s=%04x\n",a1,core->busRead16(core,strtoul(a1,0,16)));
  else if(!strcmp(cmd,"r32")) fprintf(resf,"%s=%08x\n",a1,core->busRead32(core,strtoul(a1,0,16)));
  else if(!strcmp(cmd,"pc")){ uint32_t p=0,lr=0; core->readRegister(core,"pc",&p); core->readRegister(core,"lr",&lr); fprintf(resf,"pc=%08x lr=%08x\n",p,lr);} else if(!strcmp(cmd,"r8")) fprintf(resf,"%s=%02x\n",a1,core->busRead8(core,strtoul(a1,0,16)));
 }
 fclose(resf); core->deinit(core); return 0; }
