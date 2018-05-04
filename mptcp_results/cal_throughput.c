/*
 *            README
 * 该文件用于计算指定单位时间内，多个tcp数据字段的长度和，即吞吐量
 * 输入文件为 mptcplog.c程序的输出文件
 * 输入文件名后缀需为：_out.txt， 例如：s_2_2.cap_port0_59607_out.txt
 * 程序会自动遍历所在当前目录下具有该后缀的所有文件，并处理输出相应文件
 * 
 * 
 ***输入数据格式***
 * 第一列为时间戳，第二列为tcp数据字段长度, 两列之间为Tab键，即'\t'
 * 例如：
//时间戳             数据长度
1436339533.121812	8
1436339533.121852	8
1436339533.127700	8
1436339533.137741	8
1436339533.137794	8
1436339533.137803	8

...

 ***输出数据格式***
 * 第一列为调整后的单位时间戳，第二列为该单位时间内的数据长度和
 * 例如单位时间指定为 0.01秒 (precision==2)
 * 那么由以上输入文件的数据得出的输出为：
//单位时间戳      求和后数据长度
1436339533.12	24      //3*8=24
1436339533.13	24		//两列之间用'\t'分开



encoding: utf-8
created time: 2015-07-10

  
 */


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <dirent.h> //opendir


//precision用于指定时间戳的小数点后位数
//例如 precision == 2时， 单位时间为0.01
//更改precision的值，可调节精度
// 0 < precision < 小数部分长度
#define precision 2

//文件行最大长度
#define MAX_LINE_LEN 1024

//时间戳最大长度
#define MAX_TIME_LEN 64

void calculate(char* in_file_name, char* out_file_name)
{
	FILE* fread = fopen(in_file_name,"r");
	
	//w+ 打开可读写文件，若文件存在则文件长度清为零，即该文件内容会消失。若文件不存在则建立该文件。
	FILE* fwrite = fopen(out_file_name,"w+");
	
	char line[MAX_LINE_LEN];
	
	//记录之前时间，整数部分时间和precision部分的小数部分
	char pre_time[MAX_TIME_LEN];
	pre_time[0]='\0';
	pre_time[MAX_TIME_LEN-1]='\0';
	
	//记录当前时间，整数部分时间和precision部分的小数部分
	char current_time[MAX_TIME_LEN];
	current_time[0]='\0';
	current_time[MAX_TIME_LEN-1]='\0';
	
	
	
	
	//注意：若数据长度过长，可能超过unsigned int范围
	unsigned int current_data_len = 0;
	unsigned int sum = 0;
	
	//时间长度，整数部分 + precision
	int  time_len = 0;
	
	while(1)
	{
		//line_count++;
		fgets(line, MAX_LINE_LEN, fread);
		if (feof(fread))
			break;
		
		//printf("line: %s\n", line);
		
		char* p1 = strchr(line, '.');
		char* p2 = strchr(line, '\t');
		if (p1==NULL || p2==NULL)
		{
			if (feof(fread))
				break;
			
			printf("Input data format error! or end of file\n");
			fclose(fread);
			fclose(fwrite);
			assert(0);
		}
		
		//tcp数据字段长度
		current_data_len = atoi(p2+1);
		
		time_len = p1 + precision - line + 1;
		
		strncpy(current_time, line, time_len);
		current_time[time_len]='\0';
		
		//printf ("%s\n",current_time);
	
		int i=0;
		for (i=0; i<time_len; i++)
		{
			if (current_time[i]!=pre_time[i]) 
			{
				break;
			}
		}
		
		
		//在指定精度下，当前时间和之前时间一致
		//累加 sum
		if (i==time_len)
		{
			sum += current_data_len;
		}
		
		//两次时间不一致
		//写入 单位时间戳和sum
		else 
		{
			//若pre_time[0]=='\0'，则表示读入文件第一行时，两次时间不一致
			//忽略该次不一致
			//不等于'\0'时，写入文件
			if (pre_time[0]!='\0')
			{
				//写入 单位时间戳和sum
				fprintf(fwrite, "%s\t%d\n", pre_time, sum);
			}
			
			
			//更新pre_time
			//初始化 sum
			int i=0;
			for (i=0; i<time_len; i++)
			{
				pre_time[i] = current_time[i];
			}
			pre_time[time_len]='\0';
			sum = current_data_len;
		}
		//printf("%s.%s, %u\n",second, current_time, current_data_len);
		
		
	}
	//end of file 跳出循环
	//写入最后一次
	fprintf(fwrite, "%s\t%d\n", pre_time, sum);
	
	
	
	fclose(fread);
	fclose(fwrite);
}

int main(int argc, char *argv[])
{	
	struct dirent *pDirEntry = NULL;
    DIR *pDir = NULL;
    if( (pDir = opendir("./")) == NULL )
    {
		printf("opendir failed!\n");
		return 1;
	}
    else
    {
		while( pDirEntry = readdir(pDir) )
		{
			char outfilename[64];
			
			
			//判断是否为指定类型的文件
			//该判断条件，仅判断是否含有指定字串，而不是后缀，可能存在问题
			if(strstr(pDirEntry->d_name, "_out.txt"))
			{
				int len = strlen(pDirEntry->d_name);
				len = len-8;
				strncpy(outfilename,pDirEntry->d_name,len);
				outfilename[len]='\0';
				strcat(outfilename,"_throughput.txt");
				
                printf("输入文件名：%s\t 输出文件名：%s\n",pDirEntry->d_name, outfilename);
				
				calculate(pDirEntry->d_name, outfilename);
				
				printf("------------------------------------\n");
			}
		}
		closedir(pDir);

	}       
	
	
	
	return 0;
}





